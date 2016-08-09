# -*- coding: utf-8 -*-

import re

import sys
import vcf

from genestack import Indexer, GenestackException
from genestack.bio.reference_genome.reference_genome_file import ReferenceGenome
from genestack.metainfo import StringValue, Metainfo
from genestack.utils import normalize_contig_name

# FIXME find usages and remove this constants from here
DATA_LINK = Metainfo.DATA_URL
DATA_LOCATION = Metainfo.DATA_LOCATION

EFF_FIELDS = ['Effect', 'Effect_Impact', 'Functional_Class', 'Codon_Change',
              'Amino_Acid_Change', 'Amino_Acid_length', 'Gene_Name',
              'Transcript_BioType', 'Gene_Coding', 'Transcript_ID',
              'Exon_Rank', 'Genotype_Number', 'ERRORS', 'WARNINGS']
EFF_SCHEMA_FIELDS = [('eff_' + e.lower()) for e in EFF_FIELDS]


class RecordConverter(object):
    BASE_SCHEMA = {
        'CHROM': 'contig_s',
        'LOCATION': 'location_iv',
        'START': 'start_l',
        'REF': 'ref_s_ci',
        'QUAL': 'qual_f',
        'ID': 'id_s_ci',
        'FILTER': 'filter_ss_ci',
        'ALT': 'alt_ss_ci',
        'ALT_COUNT': 'alt_len_i_ns',
        'TYPE': 'type_ss_ci'
    }

    def __init__(self, vcf_reader):
        """
        Record converter converts vcf.Record to feature.

        ``self.schema`` is filled with info from vcf.Reader.infos.

        We can not create schema by analysing record items if we create record manually.

        There are some differences in schema depending on how it was created:
           - value types
              - manual: can contain numbers, string and unicode values
              - parsed: contain only strings
           - single values
              - manual: records always contain list of values
              - parsed: have single value if it is single in schema
        """
        self.range_limit = self.__get_range_limit(vcf_reader.infos)

        self.schema = self.BASE_SCHEMA.copy()
        for info in vcf_reader.infos.values():
            if info.type == 'Float':
                suffix = 'f'
            elif info.type == 'Integer':
                suffix = 'l'
            elif info.type in ('Character', 'String'):
                suffix = 's'
            elif info.type == 'Flag':
                suffix = 'b'
            else:
                raise GenestackException('Unexpected vcf info type for {}'.format(info))

            # for single bool value num is 0
            if str(info.num) not in ('0', '1'):
                suffix += 's'
            self.schema[info.id] = 'info_%s_%s' % (info.id, suffix)

    @staticmethod
    def __get_range_limit(infos):
        """
        Return range limit from vcf.Reader.infos.

        Get low and high range for field types.
        ``None`` mean that there is no limit.
        Text searched by regular expression, wrong values will be silently ignored.
        examples:
          - (Range:1-10)  1.0, 10.0
          - (Range:-10.33)   None, 10.33
          - (Range:10-)   10.0, None
        """
        range_limit = {}
        reg = re.compile('\(Range:([0-9]*\.?[0-9]*)-([0-9]*\.?[0-9]*)\)')
        for key, val in infos.items():
            match = reg.search(val.desc)
            if match:
                range_limit[key] = tuple(float(x) if x else None for x in match.group(1, 2))
        return range_limit

    def convert_record_to_feature(self, line_id, record):
        """
        Convert vcf.Record to feature.

        :param line_id: line id in file,  first line of file has id=1
        :type line_id: long
        :param record: record
        :type record: vcf.Record
        :return:
        """
        contig = normalize_contig_name(record.CHROM)
        start = record.start
        end = record.end
        record_id = record.ID
        ref = record.REF
        substitutions = record.ALT
        quality = record.QUAL
        filter_field = record.FILTER
        info = record.INFO
        samples_format = record.FORMAT
        samples = record.samples

        data = {
            '__id__': str(line_id),
            'line_l': line_id,
            'contig_s': contig,
            'location_iv': str(start) + " " + str(end),
            'start_l': start,
            'ref_s_ci': ref,
            'qual_f': quality
        }

        if record_id != '.':
            data['id_s_ci'] = record_id
        if filter_field != '.':
            data['filter_ss_ci'] = filter_field

        data.update(self.__get_samples_info(samples_format, samples))

        alt = list()
        types = list()
        for subst in substitutions:
            sub = str(subst) if subst is not None else '.'
            alt.append(sub)
            types.append(self.__get_type(ref, sub))
        data['alt_ss_ci'] = alt
        data['alt_len_i_ns'] = len(alt)
        data['type_ss_ci'] = types

        '''For future use; I would prefer to use PyVCF methods instead of implementing my own.
           But there is a slight difference in the results. Please review if these differences are critical.
        if record.is_snp:
            data['is_snp_b'] = True
        if record.is_indel:
            data['is_indel_b'] = True
        if record.is_transition:
            data['is_transition_b'] = True
        if record.is_deletion:
            data['is_deletion_b'] = True
        if record.is_monomorphic:
            data['is_monomorphic_b'] = True
        data['var_type_s'] = record.var_type
        data['var_subtype_s'] = record.var_subtype
        '''

        for key, value in info.items():
            if value is None:
                continue
            if isinstance(value, list) and value[0] is None:
                continue

            if key not in self.schema:
                typed_key = self.__get_typed_string(key, value)
                self.schema[key] = typed_key
            typed_key = self.schema[key]

            if typed_key == 'info_EFF_ss':
                for eff_line in value:
                    # TODO Here we blindly parse snp_eff line and believe that
                    # items are in the proper order,
                    # but we have not even checked snpEff version
                    # Seems that we should check snpEff version before doing such blind parsing
                    for i, val in enumerate(re.split('\(|\)|\|', eff_line)):
                        eff_key = EFF_SCHEMA_FIELDS[i]
                        eff_typed_key = 'info_splitted_' + eff_key + '_ss'
                        data.setdefault(eff_typed_key, []).append(val)
                        self.schema[eff_key] = eff_typed_key
            # TODO info_EFF_ss is stored both as raw and as parsed,
            # need to check that nobody rely on raw value
            data[typed_key] = value
            if isinstance(value, list):
                key_base = self.__get_typed_string(key, value[0]) + '_ns'
                low_limit, high_limit = self.range_limit.get(key, (None, None))
                if low_limit:
                    value = [x for x in value if x >= low_limit]
                if high_limit:
                    value = [x for x in value if x <= high_limit]
                if value:
                    data['sorting_max_' + key_base] = max(value)
                    data['sorting_min_' + key_base] = min(value)
        return data

    def __get_samples_info(self, samples_format, samples):
        info = {}
        format_list = samples_format.split(':') if samples_format is not None else []
        for s in samples:
            info.setdefault('samples_info_names_ss_ci', []).append(s.sample)
            for f in format_list:
                val = self.__get_attribute_as_string(s.data, f)
                info.setdefault('samples_info_' + f + '_ss', []).append(val)
        return info

    @staticmethod
    def __get_attribute_as_string(data, attr):
        val = getattr(data, attr, None)
        if val is None:
            return ''
        if isinstance(val, list):
            return ",".join(map(str, val))
        return str(val)

    @staticmethod
    def __get_typed_string(key, value):
        """
        Add solr suffix depending on value type

        :param key: key
        :type key: str
        :param value: corresponding value
        :type value: any
        :return: solr key string
        :rtype: str
        """
        key = 'info_' + key
        list_suffix = 's' if isinstance(value, list) else ''
        v = value[0] if list_suffix else value

        if v is None:
            return None

        if isinstance(v, basestring):
            suffix = '_s'
        elif isinstance(v, bool):
            suffix = '_b'
        elif isinstance(v, (int, long)):
            suffix = '_l'
        elif isinstance(v, float):
            suffix = '_f'
        else:
            raise GenestackException("Unknown type for key %s: %s (%s)" % (key, v, type(v)))
        return key + suffix + list_suffix

    @staticmethod
    def __get_type(ref, alt):
        if alt == '.':
            return 'MR'
        if len(ref) == 1 and len(alt) == 1:
            return 'SNP'
        elif len(ref) == len(alt):
            return 'MNP'
        elif len(ref) < len(alt):
            return 'INS'
        else:
            return 'DEL'


class VariationIndexer(object):
    INDEXING_CHUNK_SIZE = 4000
    QUERY_CHUNK_SIZE = 100

    MAX_LINE_KEY = 'genestack.initialization:maxLine'

    def __init__(self, target_file, reference_genome=None):
        self.target_file = target_file
        if reference_genome is None:
            reference_genome = target_file.resolve_reference(
                target_file.REFERENCE_GENOME_KEY, ReferenceGenome
            )
        assert reference_genome is not None, "No reference genome found"
        self.reference_genome = reference_genome
        self.__schema = None

    @property
    def schema(self):
        sys.stderr.write('"schema" attribute is deprecated, use RecordConvertor schema instead\n')
        return self.__schema

    def get_indexing_line_from(self):
        line_from_value = self.target_file.get_metainfo().get_first_string(VariationIndexer.MAX_LINE_KEY)
        try:
            return int(line_from_value) if line_from_value is not None else 0
        except ValueError:
            return 0

    def set_max_line(self, line_id):
        self.target_file.replace_metainfo_value(VariationIndexer.MAX_LINE_KEY, StringValue(str(line_id)))

    def iterate_features(self, vcf_reader, record_converter=None, line_from=0):
        """
        Returns generator over features corresponding to vcf record in file.
        If ``record_converter`` is not specified uses record converter based on this vcf file.

        :param vcf_reader: vcf reader
        :type vcf_reader: vcf.Reader
        :param record_converter: converter from record to feature
        :type record_converter: RecordConverter
        :param line_from: first line that should be returned, use 0 for the whole file
        :return: generator
        """
        if record_converter is None:
            record_converter = RecordConverter(vcf_reader)
        self.__schema = record_converter.schema
        for line_id, record in enumerate(vcf_reader, start=1):
            if line_from > line_id:
                continue
            yield line_id, record_converter.convert_record_to_feature(line_id, record)

    def get_indexer(self, file_to_index, record_converter=None):
        """
        Return context manager to index records.
        This indexer has two methods:

          - ``index_record`` which accepts line_number and record
          - ``index_feature`` which accepts feature

        ``index_record`` can be called only if record_converter is specified.

        :param file_to_index: Genestack file instance
        :param record_converter: record converter
        :return: indexer
        """

        process_features = self.process_features
        set_max_line = self.set_max_line
        set_initialization_version = self.__set_initialization_version

        class RecordIndexer(object):
            def __init__(self, file_to_index, record_converter):
                self.__file = file_to_index
                self.__inside_context = False
                self.features = []
                self.raw_features = []
                self.record_converter = record_converter
                self.__last_feature_line_id = None

            def __enter__(self):
                set_initialization_version()
                self.__inside_context = True
                self.indexer = Indexer(file_to_index)
                self.indexer.__enter__()
                return self

            def __exit__(self, exc_type, exc_val, exc_tb):
                self.__flush(force=True)
                self.indexer.__exit__(exc_type, exc_val, exc_tb)
                self.__inside_context = False

            def index_record(self, line, record):
                if not self.record_converter:
                    raise GenestackException('Indexing record only possible if record converter is specified')
                feature = self.record_converter.convert_record_to_feature(line, record)
                self.index_feature(feature)

            def index_feature(self, feature):
                if not self.__inside_context:
                    raise GenestackException('RecordIndexer object must be used only inside a "with" statement')
                self.raw_features.append(feature)
                self.__last_feature_line_id = feature['line_l']
                self.__flush()

            def __flush(self, force=False):
                limit = 0 if force else (VariationIndexer.QUERY_CHUNK_SIZE - 1)
                if len(self.raw_features) > limit:
                    self.features.extend(process_features(self.raw_features))
                    self.raw_features = []

                limit = 0 if force else (VariationIndexer.INDEXING_CHUNK_SIZE - 1)
                if len(self.features) > limit:
                    self.indexer.index_records(self.features)
                    self.features = []
                    set_max_line(self.__last_feature_line_id)

        return RecordIndexer(file_to_index, record_converter)

    def create_index(self, file_name):
        """
        Create index for vcf file.

        Indexing progress is stored in metainfo, if file started for first time it is empty
        and whole file will be indexing.  Then record is send to server it metainfo will be updated.
        Rerunning file in case of fail will proceed indexing from last point.

        :param file_name: existing name of vcf file
        :type file_name: str
        :return: None
        """
        with open(file_name) as f, self.get_indexer(self.target_file, record_converter=None) as indexer:
            vcf_reader = vcf.Reader(f)
            record_converter = RecordConverter(vcf_reader)
            for line_id, feature in self.iterate_features(vcf_reader, record_converter=record_converter,
                                                          line_from=self.get_indexing_line_from()):
                indexer.index_feature(feature)

    def __set_initialization_version(self):
        """
        Set version of initialization. This key required to support different versions.
        """
        self.target_file.replace_metainfo_value('genestack.indexing:version', StringValue('splitEffAnnotations'))

    # TODO: Remove this method if we decide not to index ReferenceGenome data
    def __append_genome_features(self, mutation_list):
        # code removed at commit f64cdf12ddd9a64ec5cbfdebaa1d01be24224239
        pass

    def process_features(self, features_list):
        """
        This method can be overridden in children to process features before adding them to index.

        :param features_list: list of features to be processed
        :return: processed feature list
        """
        # hack to support old api
        if hasattr(self, 'process_record'):
            import sys
            sys.stderr.write('Warning! "process_record" method is deprecated use "process_features" instead\n')
            return self.process_record(features_list)
        else:
            return features_list
