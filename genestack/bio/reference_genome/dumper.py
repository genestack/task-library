# -*- coding: utf-8 -*-
import os


class FastaDumper(object):
    """
    Class for dumping fasta data to file.

    Create a files name composed from contig name followed by
     the index of this file among all files for the contig.

    Example: 5th nucleotide of Chromosome will be placed in a file called "Chromosome_0",
     10005th  will be placed in a file called "Chromosome_1" file etc.
    """
    BUFFER_SIZE = 10000

    def __init__(self, current_folder):
        self.current_folder = current_folder
        self.prefix = None
        self.buffer = ''
        self.index = 0

    def _dump(self):
        """
        Dump buffer to the file in current folder named with ``index`` value and
        increment ``index`` value by 1.

        If buffer is empty does nothing,
        If buffer is bigger then self.BUFFER_SIZE, dump only self.BUFFER_SIZE.
        """
        if not self.buffer or not self.prefix:
            return
        file_name = '%s_%s' % (self.prefix, self.index)
        with open(os.path.join(self.current_folder, file_name), 'w') as f:
            f.write(self.buffer[:self.BUFFER_SIZE])
        self.index += 1
        self.buffer = self.buffer[self.BUFFER_SIZE:]

    def flush(self):
        """
        Save all data from buffer to file.

        :return: None
        """
        if self.prefix:
            self._dump()
            self.index = 0
            self.prefix = None

    def set(self, prefix):
        """
        Flush current data and set new suffix.

        :param prefix: current contig name
        :type prefix: str
        :return: None
        """
        self.flush()
        self.prefix = prefix

    def add(self, text):
        """
        Add chunk of data to the current folder.
        If total length of all chunks in buffer is greater than self.BUFFER_SIZE
        then they will be dumped into a file.

        :param text: text to dump
        :type text: str
        """
        self.buffer += text
        if len(self.buffer) > self.BUFFER_SIZE:
            self._dump()
