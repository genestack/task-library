# -*- coding: utf-8 -*-

import os
import shlex

from genestack.frontend_object import StorageUnit
from genestack.genestack_exceptions import GenestackException
from genestack.utils import opener, DumpData, normalize_contig_name

# this constants should be same as in java code
VARIABLE_STEP = 1
FIXED_STEP = 2


def parse_line_params(text):
    res = {}
    items = shlex.split(text)
    for item in items:
        item_split = item.split('=', 1)
        if len(item_split) == 2:
            res[item_split[0]] = item_split[1]
    return res


def parse_float(text):
    try:
        return float(text)
    except ValueError:
        raise GenestackException('Cannot parse value "%s" to float' % text)


def parse_int(text):
    try:
        return int(text)
    except ValueError:
        raise GenestackException('Cannot parse value "%s" to int' % text)


class Step(object):
    step_type = None

    def __init__(self, line, track_number):
        self._line = line  # used for error messages
        self.params = parse_line_params(line)
        self.items = []
        self.track_number = track_number
        self.set_contig()
        self.set_span()

    def update(self, line):
        self.items.append(line)

    def set_contig(self):
        chrom = self.params.get("chrom")
        if not chrom:
            raise GenestackException('No field "chrom" in declaration: %s' % self._line)
        self.contig = normalize_contig_name(chrom)

    def set_span(self):
        span = parse_int(self.params.get('span', 1))
        if span < 1:
            raise GenestackException('Span value should be positive integer, got: %s' % span)
        self.span = span

    def add_dump_data(self, dd):
        dd.put_byte(self.step_type)
        dd.put_int(self.span)
        dd.put_int(self.track_number)
        dd.put_int(len(self.items))


class VariableStep(Step):
    step_type = VARIABLE_STEP

    def update(self, line):
        try:
            pos, score = line.split(' ')
        except ValueError:
            raise GenestackException('Line should have two fields: %s' % line)

        self.items.append((parse_int(pos) - 1, parse_float(score)))

    def add_dump_data(self, dd):
        super(VariableStep, self).add_dump_data(dd)
        min_start = 0
        for pos, val in self.items:
            if pos < min_start:
                raise GenestackException('All positions specified in the input data must be in ascending order')
            min_start = pos
            dd.put_long(pos)
            dd.put_float(val)

    def get_start(self):
        return self.items[0][0]

    def get_end(self):
        return self.items[-1][0] + self.span


class FixedStep(Step):
    step_type = FIXED_STEP

    def __init__(self, line, track_number):
        super(FixedStep, self).__init__(line, track_number)
        self.set_step()
        self.set_start()

    def set_step(self):
        step = self.params.get('step')
        if not step:
            raise GenestackException('No field "step" in declaration: %s' % self._line)
        step = parse_int(step)
        if step < 1:
            raise GenestackException('Step value should be positive integer, got: %s' % step)
        self.step = step

    def set_start(self):
        start = self.params.get('start')
        if not start:
            raise GenestackException('No field "start" in declaration: %s' % self._line)
        start = parse_int(start)
        if start < 1:
            raise GenestackException('Start value should be positive integer, got: %s' % start)
        self.start = start - 1

    def add_dump_data(self, dd):
        super(FixedStep, self).add_dump_data(dd)
        dd.put_long(self.get_start())
        dd.put_int(self.step)
        for item in self.items:
            dd.put_float(parse_float(item))

    def get_start(self):
        return self.start

    def get_end(self):
        return self.get_start() + self.step * (len(self.items) - 1) + self.span


class WigTrack(object):
    def __init__(self, track_line=''):
        self.track_line = track_line

    def add_dump_data(self, fs):
        fs.write(self.track_line)
        fs.write('\n')


class WIGIndexer:
    INDEX_LOCATION = 'genestack.location:index_tracks'
    WIG_INDEX_LOCATION = 'genestack.location:index_wig'
    CONTIG_CACHE_LOCATION = 'genestack.location:index_cache'

    READ_LIMIT = 10 * (2 ** 20)  # 10 mb

    def __init__(self, wig, result_folder='result'):
        self.wig = wig
        self.result_folder = result_folder
        if not os.path.exists(self.result_folder):
            os.makedirs(os.path.abspath(self.result_folder))
        self.result_contig_cache_folder = "contig.cache"
        if not os.path.exists(self.result_contig_cache_folder):
            os.makedirs(os.path.abspath(self.result_contig_cache_folder))
        self.result_wig_file = os.path.join(self.result_folder, 'wig.data')
        self.result_tracks_file = os.path.join(self.result_folder, 'tracks.txt')

    def dump_steps(self, steps):
        if not steps:
            return
        steps.sort(key=lambda x: x.contig)
        dd = DumpData()
        for step in steps:
            offset = dd.size
            step.add_dump_data(dd)
            size = dd.size - offset
            self.index.setdefault(step.contig, []).append([step.get_start(), step.get_end(), offset, size])

        with open(self.result_wig_file, 'wb+') as fs:
            dd.dump_to_file(fs)

    def final_dump(self, tracks):
        with open(self.result_tracks_file, 'w') as fs:
            for track in tracks:
                track.add_dump_data(fs)

        for contig, indices in self.index.iteritems():
            dd = DumpData()
            indices.sort(key=lambda x: x[0])
            for start, end, offset, size in indices:
                dd.put_long(start)
                dd.put_long(end)
                dd.put_long(offset)
                dd.put_int(size)
            path = os.path.join(self.result_contig_cache_folder, contig)
            with open(path, 'wb') as fs:
                dd.dump_to_file(fs)

    def create_index(self, source_wig_file):
        self.index = {}
        tracks = []
        steps = []

        limit = self.READ_LIMIT

        with opener(source_wig_file) as fs:
            for line in fs:
                line = line.strip()

                if line and not line.startswith('#') and not line.startswith("browser"):
                    limit -= len(line)
                    if limit <= 0:
                        self.dump_steps(steps[:-1])  # don`t dump last step
                        steps = steps[-1:]
                        limit = self.READ_LIMIT

                    if line.startswith('track'):
                        tracks.append(WigTrack(line))
                    elif line.startswith("variableStep"):
                        if not tracks:
                            tracks.append(WigTrack())
                        steps.append(VariableStep(line, len(tracks) - 1))
                    elif line.startswith("fixedStep"):
                        if not tracks:
                            tracks.append(WigTrack())
                        steps.append(FixedStep(line, len(tracks) - 1))
                    else:
                        steps[-1].update(line)

        self.dump_steps(steps)
        self.final_dump(tracks)

        self.wig.PUT(self.INDEX_LOCATION, StorageUnit(self.result_tracks_file))
        self.wig.PUT(self.WIG_INDEX_LOCATION, StorageUnit(self.result_wig_file))
        self.wig.PUT(self.CONTIG_CACHE_LOCATION, StorageUnit(self.result_contig_cache_folder))
