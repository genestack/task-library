# -*- coding: utf-8 -*-

from zipfile import ZipFile, ZIP_DEFLATED


class FastaZipDumper(object):
    """
    used to dump fasta data to file.

    for each contig in fasta files we make new file with <contig_name>.zip

    zip entries named for number of BUFFER_SIZE added.

    for example 5th nucleotide is inside "0" file, 10005th is inside "1" file etc.
    """
    BUFFER_SIZE = 10000

    def __init__(self):
        self.current_file = None
        self.buffer = ''
        self.index = 0

    def _dump(self):
        """
        If buffer is empty this method does nothing;
        otherwise dumps buffer to the next ZIP entry named with current `index`
        value and increments `index` value by 1.
        Method writes self.BUFFER_SIZE symbols from buffer (or the whole buffer
        if its size is less than self.BUFFER_SIZE).
        """
        if not self.buffer or not self.current_file:
            return
        self.current_file.writestr(
            str(self.index),
            self.buffer[:self.BUFFER_SIZE],
            ZIP_DEFLATED
        )
        self.index += 1
        self.buffer = self.buffer[self.BUFFER_SIZE:]

    def flush(self):
        """
        Saves all data from buffer to file. Close file.
        :return:
        """
        if self.current_file:
            self._dump()
            self.index = 0
            self.current_file.close()
            self.current_file = None

    def set(self, file_path):
        """
        Flush current file and set new current file.

        :param file_path: path to the new file to open
        """
        self.flush()
        self.current_file = ZipFile(file_path, 'w')

    def add(self, text):
        """
        Add chunk of data to the current file.
        If total length of all chunks in buffer is more then self.BUFFER_SIZE
        dumps it to file.
        :param text: text to dump
        """
        self.buffer += text
        if len(self.buffer) > self.BUFFER_SIZE:
            self._dump()
