# -*- coding: utf-8 -*-

import json
import os
import shutil
import subprocess
import sys

from genestack.genestack_exceptions import GenestackException
from genestack.frontend_object import StorageUnit
from genestack.genestack_indexer import Indexer

from genestack.bio.annotation_utils import determine_annotation_file_format, GTF, GFF3

from genestack.bio.reference_genome.dumper import FastaDumper
from genestack.metainfo import StringValue
from genestack.utils import DumpData, normalize_contig_name, opener, truncate_sequence_str


def get_qualifier(feature, attribute_key):
    return feature.qualifiers.get(attribute_key, [None])[0]

INDEXING_VERSION = 'genestack.indexing:version'


def _handle_gtf_feature(contig, feature, genes):
    attribute_holder = feature.sub_features[0] if feature.sub_features else feature
    # all sub features belong to the same transcription => to the same gene
    features_list = feature.sub_features if feature.sub_features else [feature]

    subfeatures = [SubFeature(int(subfeature.location.start),
                              int(subfeature.location.end),
                              subfeature.strand,
                              subfeature.type) for subfeature in features_list]

    gene_name = get_qualifier(attribute_holder, 'gene_name')
    transcript_name = get_qualifier(attribute_holder, 'transcript_name')
    gene_id = get_qualifier(attribute_holder, 'gene_id')
    transcript_id = get_qualifier(attribute_holder, 'transcript_id')

    genes.add(contig,
              gene_name,
              gene_id,
              transcript_name,
              transcript_id,
              int(feature.location.start),
              int(feature.location.end),
              subfeatures)


def _handle_gff3_feature(contig, feature, genes):
    if 'gene' not in feature.type and 'pseudogenic' not in feature.type:
        return
    gene_id = get_qualifier(feature, 'gene_id') or get_qualifier(feature, 'ID')
    gene_name = get_qualifier(feature, 'Name')
    genes.add(contig,
              gene_name,
              gene_id,
              None,
              None,
              int(feature.location.start),
              int(feature.location.end),
              None)
    for sub_feature in feature.sub_features:
        transcript_id = get_qualifier(sub_feature, 'transcript_id') or get_qualifier(sub_feature, 'ID')
        transcript_name = get_qualifier(sub_feature, 'Name')
        sub_sub_features = [SubFeature(int(subfeature.location.start),
                                       int(subfeature.location.end),
                                       subfeature.strand,
                                       subfeature.type) for subfeature in sub_feature.sub_features]
        genes.add(contig,
                  gene_name,
                  gene_id,
                  transcript_name,
                  transcript_id,
                  int(sub_feature.location.start),
                  int(sub_feature.location.end),
                  sub_sub_features)


class Gene(object):
    def __init__(self):
        self.name = None
        self.transcripts = TranscriptsCollection()

    def update(self, contig, gene_name, gene_id, transcript_name, transcript_id, start, end, subfeatures):
        if self.name is None:
            self.name = gene_name or gene_id
            self.contig = contig
            self.id = gene_id
            self.start = start
            self.end = end
        else:
            self.start = min(self.start, start)
            self.end = max(self.end, end)
        if transcript_name or transcript_id:
            self.transcripts.add(transcript_name, transcript_id, start, end, subfeatures)
        # return self to make chained calls
        return self


class GenesCollection(dict):
    def add(self, contig, name, gene_id, transcript_name, transcript_id, start, end, subfeatures):
        return self.setdefault(gene_id, Gene()).update(
            contig, name, gene_id, transcript_name, transcript_id,
            start, end, subfeatures
        )

    def __str__(self):
        return "Genes collection with %s genes" % len(self)


class Transcript(object):
    def __init__(self):
        self.name = None

    def update(self, name, transcript_id, start, end, subfeatures):
        if self.name is None:
            self.name = name or transcript_id
            self.id = transcript_id
            self.start = start
            self.end = end
            self.subfeatures = subfeatures
        else:
            self.start = min(self.start, start)
            self.end = max(self.end, end)
            self.subfeatures.extend(subfeatures)
        # return self to make chained calls
        return self


class TranscriptsCollection(dict):
    def add(self, name, transcript_id, start, end, subfeatures):
        return self.setdefault(transcript_id, Transcript()).update(
            name, transcript_id, start, end, subfeatures
        )


class SubFeature(object):
    def __init__(self, start, end, strand, kind):
        self.start = start
        self.end = end
        self.strand = strand if strand is not None else 2
        self.kind = kind


class ReferenceGenomeIndexer:
    INDEX_FASTA_LOCATION = 'genestack.location:index_fasta'
    INDEX_FASTA_CACHE_LOCATION = 'genestack.location:index_fasta_cache'

    TYPE_SUFFIXES = {
        'gene': '/G',
        'transcript': '/T',
    }

    def __init__(self, genome, result_dir='result'):
        """
        :param genome:
        :type genome: genestack.bio.ReferenceGenome
        :param result_dir: directory to store files
        :type result_dir: str
        :return:
        """
        # setup paths:
        self.genome = genome
        self.result_dir = result_dir
        if not os.path.exists(self.result_dir):
            os.makedirs(os.path.abspath(self.result_dir))

        self.result_fasta_contigs_index_path = os.path.join(self.result_dir, 'fasta.data')
        self.result_fasta_cache_folder = os.path.join(self.result_dir, 'fasta.cache')

        # we ignore all contigs from annotation, that has no fasta file
        self.allowed_contigs = set()

        if os.path.exists(self.result_fasta_cache_folder):
            shutil.rmtree(self.result_fasta_cache_folder)
        os.mkdir(self.result_fasta_cache_folder)

    def index_features(self, source_annotations_file_path):
        # avoid crash then using pypy
        import BCBio.GFF
        source_annotations_file = open(source_annotations_file_path)
        annotation_format = determine_annotation_file_format(source_annotations_file_path)

        if annotation_format == GFF3:
            handle_feature = _handle_gff3_feature
        elif annotation_format == GTF:
            handle_feature = _handle_gtf_feature
        else:
            raise GenestackException('Annotation format is not supported: %s' % annotation_format)

        # The parser will attempt to smartly break up the file at requested number of lines
        # and would continue until the entire feature region is read.
        # A nested coding feature: gene -> transcript -> CDS/exon/intron
        current_contig = None

        annotation_contigs = set()  # all contigs from annotation

        with Indexer(self.genome) as indexer:
            for record in BCBio.GFF.parse(source_annotations_file, target_lines=2000):
                contig = record.id
                annotation_contigs.add(contig)
                if contig not in self.allowed_contigs:
                    continue
                # contig can not be None here because self.allowed_contigs never contains None

                if current_contig != contig:
                    if current_contig:
                        indexer.index_records(self.create_index_records(genes))
                    current_contig = contig
                    genes = GenesCollection()

                # collect all genes and transcripts from the portion of GTF. First item always gene
                for feature in record.features:
                    handle_feature(contig, feature, genes)
            if current_contig:
                indexer.index_records(self.create_index_records(genes))
            if not annotation_contigs.intersection(self.allowed_contigs):
                msg = ('Error: '
                       'contig names from the genome sequence and annotation '
                       'totally differ (have no common items)\n'
                       'Contigs present in sequence: %s\n'
                       'Contigs present in annotation: %s\n' % (
                           truncate_sequence_str(self.allowed_contigs),
                           truncate_sequence_str(annotation_contigs))
                       )
                sys.stderr.write(msg)


    @staticmethod
    def create_index_records(genes):
        def make_index_record(record_id, name, contig, start, end, record_type, gene_id=None, subfeatures_list=None):
            feature_id = str(record_id)
            doc_id = feature_id + ReferenceGenomeIndexer.TYPE_SUFFIXES[record_type]
            data = {
                '__id__': doc_id,
                'id_s_ci': feature_id,
                'name_s_ci': name,
                'contig_s_ci': contig,
                'location_iv': str(start) + " " + str(end),
                'start_l': start,
                'type_s': record_type
            }
            if gene_id is not None:
                data['parentGeneId_s_ci'] = gene_id
            if subfeatures_list is not None:
                data['subfeatures_ss'] = subfeatures_list
            return data

        feature_list = []
        for g in genes.itervalues():
            for t in g.transcripts.itervalues():
                subfeatures = [json.dumps({
                    'kind': s.kind,
                    'start': s.start,
                    'end': s.end,
                    'strand': s.strand
                }) for s in t.subfeatures]

                feature_list.append(make_index_record(
                    t.id, t.name, g.contig, t.start, t.end, "transcript",
                    gene_id=g.id, subfeatures_list=subfeatures
                ))

            feature_list.append(make_index_record(g.id, g.name, g.contig, g.start, g.end, "gene"))
        return feature_list

    def processing_fasta(self, source_fasta_file_list):
        """
        Create index for fasta file.

        A zip archive with files,
        which names are composed using a normalized contig name and a number starting from "0".
        Each file contains 10000 nucleotides or less.

        Fill list of contigs that will be use for annotation indexing.

        :param source_fasta_file_list: list fo source fasta file paths
        :type source_fasta_file_list: list[str]
        :return: None
        """
        items = []
        fasta_dumper = FastaDumper(self.result_fasta_cache_folder)

        for file_name in source_fasta_file_list:
            offset = 0
            with opener(file_name) as sequenceFile:
                first = sequenceFile.read(1)
                if first != '>':
                    raise GenestackException('File "%s" is not a sequence file' % file_name)
                else:
                    sequenceFile.seek(0)

                for line in sequenceFile:
                    if line.startswith('>'):
                        header = line[1:].split()
                        name = header[0]
                        offset += len(line)
                        items.append([name, 0])
                        self.allowed_contigs.add(name)
                        fasta_dumper.set(normalize_contig_name(name))
                    else:
                        res = line.strip()
                        items[-1][1] += len(res)
                        fasta_dumper.add(res)
        fasta_dumper.flush()

        archive_name = self.result_fasta_cache_folder + '.zip'
        cmd = ['zip', '-rjq', archive_name, self.result_fasta_cache_folder]
        subprocess.check_call(cmd)

        items.sort(key=lambda x: x[0])
        dd = DumpData()
        for name, length in items:
            dd.put_text(name)
            dd.put_long(length)
        with open(self.result_fasta_contigs_index_path, 'wb') as fasta_dump_file:
            dd.dump_to_file(fasta_dump_file)
        self.genome.PUT(self.INDEX_FASTA_CACHE_LOCATION, StorageUnit(archive_name))
        self.genome.PUT(self.INDEX_FASTA_LOCATION, StorageUnit(self.result_fasta_contigs_index_path))

    def create_index(self, fasta_paths, annotation_path):
        annotation_format = determine_annotation_file_format(annotation_path)
        if annotation_format not in [GTF, GFF3]:
            raise GenestackException('Unsupported annotation file format: %s' % annotation_format)

        self.genome.add_metainfo_value(INDEXING_VERSION, StringValue('2'))
        self.processing_fasta(fasta_paths)
        self.index_features(annotation_path)
