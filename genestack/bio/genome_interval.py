# -*- coding: utf-8 -*-

from genestack.java import java_object


class GenomeInterval:
    def __init__(self, contig_name, interval_from, interval_to):
        self.contig_name = contig_name
        self.interval_from = interval_from
        self.interval_to = interval_to

    def get_java_object(self):
        return java_object('com.genestack.bio.files.GenomeInterval', {
            'contigName': self.contig_name,
            'from': self.interval_from,
            'to': self.interval_to
        })
