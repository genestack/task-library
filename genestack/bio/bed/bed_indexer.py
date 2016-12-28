# -*- coding: utf-8 -*-

import os
import struct
import subprocess
from itertools import izip
from tempfile import mkdtemp

import validate
from genestack.frontend_object import StorageUnit
from genestack.genestack_exceptions import GenestackException
from genestack.metainfo import StringValue
from genestack.utils import opener, normalize_contig_name

validators = [validate.text_validator,
              validate.number_validator,
              validate.number_validator,
              validate.text_validator,
              validate.float_validator,  # Validate score just as float.
              validate.no_validate,      # This field should be validated but we must handle some bad bed.
              validate.number_validator,
              validate.number_validator,
              validate.rgb_validator,
              validate.number_validator,
              validate.block_validator,
              validate.block_validator
              ]

names = ['contig name',
         'start',
         'end',
         'name',
         'score',
         'strand',
         'thickStart',
         'thickEnd',
         'itemRgb',
         'blockCount',
         'blockStart',
         'blockEnd'
         ]


FEATURE_POSSIBLE_LENGTH = [3, 4, 5, 6, 8, 9, 12]


def validate_feature(feature):
    """
    Make single feature validation, raises :py:class:`~genestack.GenestackException`.

    :param feature: list of fields
    :type feature: list[str]

    raises: GenestackException
    """
    feature_length = len(feature)

    # it is ok if bed file has more fields then expected
    if feature_length not in FEATURE_POSSIBLE_LENGTH and feature_length < 12:
        raise GenestackException('Feature has wrong number of fields %s' % feature)
    for name, validator, field in izip(names, validators, feature):
        validator(field, name)

    if feature_length == 12:
        block_size = int(feature[9])
        if block_size != len(feature[10].split(',')) or block_size != len(feature[11].split(',')):
            raise GenestackException('Number of blocks does not match number of sizes')


class BEDIndexer(object):
    CONTIG_CACHE_LOCATION = 'genestack.location:index_cache'
    TRACKS_INDEX_LOCATION = 'genestack.location:tracks'
    INDEXING_VERSION_METAINFO_KEY = "genestack.indexing:version"
    VERSION = '1'

    def __init__(self, bed, output_dir=None):
        self.bed = bed
        self.output_dir = output_dir or os.getcwd()
        output_temp_dir = mkdtemp(prefix="bed_init_", dir=self.output_dir)
        self.output = os.path.join(output_temp_dir, 'file.bed')
        self.tracks = os.path.join(output_temp_dir, 'tracks.txt')
        self.index_cache_folder = os.path.join(output_temp_dir, 'index.cache')
        if not os.path.exists(self.index_cache_folder):
            os.makedirs(os.path.abspath(self.index_cache_folder))

    def create_index(self, bed_path):
        """
        Do all initialization work
        When process finished next field can be used to PUT data:

            self.index_cache_folder  # folder there index files stored
            self.output  path to sorted bam file
            result.tracks path to file there track info are stored

        """
        track_feature_length = None  # check to test all features in track has same length
        tracks = []
        track_file = None

        with opener(bed_path) as f:
            for line in f:
                line = line.strip()
                # TODO: NP: does this mean we just ignore browser instructions?
                # SA: this is ucsc.edu special attributes for their genome browser
                if line.startswith('browser') or line.startswith('#') or not line:
                    continue
                if line.startswith('track'):
                    # an array of size = size of file?
                    tracks.append(line)
                    if track_file is not None:
                        track_file.close()
                    track_file = open(self._get_track_path(len(tracks) - 1), 'w')
                    track_feature_length = None
                else:
                    if not tracks:
                        tracks.append('track')
                        track_file = open(self._get_track_path(len(tracks) - 1), 'w')
                        track_feature_length = None
                    feature = line.split('\t')
                    feature_length = len(feature)

                    if track_feature_length is None:
                        track_feature_length = feature_length
                        if feature_length < 3:
                            raise GenestackException('Not enough fields in feature: %s' % feature)
                    else:
                        if feature_length != track_feature_length:
                            # TODO: better message
                            raise GenestackException('Different number of fields: %s != %s' % (feature_length,
                                                                                               track_feature_length))

                    feature[0] = normalize_contig_name(feature[0])
                    if feature_length >= 12:
                        # TODO: NP: why? could you please explain this code?
                        # This is not described in format but our example contains trailing comas at this blocks.
                        # http://genome.ucsc.edu/FAQ/FAQformat.html#format1
                        feature[10] = feature[10].strip(', ')
                        feature[11] = feature[11].strip(', ')

                    validate_feature(feature)
                    track_file.write('\t'.join(feature))
                    track_file.write('\n')

        if track_file is not None:
            track_file.close()
        # at this stage all the data is stored in files (one for each track: `track_%s`, without headers)

        for i in xrange(len(tracks)):
            subprocess.check_call(['sort', '-k1,1', '-k2,2n', '-o', self._get_track_path(i), self._get_track_path(i)])

        offset = 0

        with open(self.output, 'w') as f:

            for track_index, track in enumerate(tracks):
                f.write(track)
                f.write('\n')
                offset += len(track) + 1

                last_contig = None
                block = None

                with open(self._get_track_path(track_index)) as track_features:
                    for line in track_features:
                        f.write(line)
                        feature = line.split('\t')
                        contig = feature[0]
                        if contig != last_contig:
                            self._dump_block_to_file(block, track_index)
                            block = Block(contig)
                            last_contig = contig
                        size = len(line)
                        block.add(feature[1], feature[2], offset, size)
                        offset += size

                    self._dump_block_to_file(block, track_index)

        with open(self.tracks, "w") as f:
            for track in tracks:
                f.write(track)
                f.write('\n')

        self.bed.add_metainfo_value(self.INDEXING_VERSION_METAINFO_KEY, StringValue(self.VERSION))
        self.bed.PUT(self.bed.DATA_LOCATION, StorageUnit(self.output))
        self.bed.PUT(self.CONTIG_CACHE_LOCATION, StorageUnit(self.index_cache_folder))
        self.bed.PUT(self.TRACKS_INDEX_LOCATION, StorageUnit(self.tracks))

    def _dump_block_to_file(self, block, index):
        if block is None:
            return
        index_output = os.path.join(self.index_cache_folder, '%s.%s.index' % (index, block.name))
        with open(index_output, "wb") as index_file:
            block.write(index_file)

    @staticmethod
    def _get_track_path(track_index):
        return "track_%s" % track_index


class Block(object):
    MAX_ITEMS = 100

    def __init__(self, contig_name):
        self.name = contig_name
        self.intervals = []
        self.counter = 0

    def get_start(self):
        return self.intervals[0][0]

    def get_end(self):
        return self.intervals[-1][1]

    def add(self, start, end, offset, size):
        start = long(start)
        end = long(end)
        if start > end:
            start, end = end, start

        if not self.intervals:
            self.intervals.append([])
        if self.counter >= self.MAX_ITEMS:
            self.intervals.append([])
            self.counter = 0

        block = self.intervals[-1]
        self.counter += 1
        if not block:
            block.extend([start, end, offset, size])
        else:
            block[1] = end
            block[3] += size

    def __repr__(self):
        return "<Block: %s %s-%s>" % (self.name, self.get_start(), self.get_end())

    def write(self, f):
        for interval in self.intervals:
            if interval:
                data = struct.pack('>qqqi', *interval)  # long+long+long+int
                f.write(data)

    def write_text(self, f):
        for interval in self.intervals:
            if interval:
                data = "%s %s %s %s\n" % interval
                f.write(data)
