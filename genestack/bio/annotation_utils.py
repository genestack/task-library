# -*- coding: utf-8 -*-
import os

from plumbum import local
import re

from genestack.cla import Toolset, RUN
from genestack.compression import get_last_non_archive_extension, decompress_file
from genestack.genestack_exceptions import GenestackException
from genestack.utils import get_unique_name, makedirs_p
from shutil import move, copy


GFF2 = 'GFF2'
GTF = 'GTF'
GFF3 = 'GFF3'


CUFFLINKS_VERSION = '2.2.1'

AVAILABLE_ANNOTATION_FORMATS = (GFF2, GFF3, GTF)


def determine_annotation_file_format(annotation_path):
    """
    Return enum constant that represents annotation file format.

    :param annotation_path: path to annotation file
    :type annotation_path: str
    :return: annotation format constant
    :rtype: str
    """
    file_extension = get_last_non_archive_extension(annotation_path)
    if file_extension == '.gff3':
        return GFF3
    elif file_extension == '.gtf':
        return GTF
    elif file_extension == '.gff':
        decompressed_file_path = decompress_file(annotation_path, remove_source=False)
        try:
            with open(decompressed_file_path) as f:
                first_line = f.readline()
            match_object = re.match('##gff-version\s+(\S+)', first_line)
            if match_object:
                version = match_object.group(1)
                if version == '3':
                    return GFF3
                else:
                    raise GenestackException(
                        'Unsupported gff version %s in file %s' % (version, annotation_path)
                    )
            return GFF2
        finally:
            if os.path.abspath(decompressed_file_path) != os.path.abspath(annotation_path):
                try:
                    os.remove(decompressed_file_path)
                except OSError:
                    pass
    else:
        raise GenestackException('Unknown annotation file format %s' % annotation_path)


def _move(file_name, dest_folder, remove_source=True):
    if dest_folder:
        dest = os.path.join(dest_folder, os.path.basename(file_name))
        if remove_source:
            move(file_name, dest)
        else:
            copy(file_name, dest)
    else:
        dest = file_name
    return dest


def get_converter(annotation_fmt_from, annotation_fmt_to):
    """
    Return converter function.

    :param annotation_fmt_from: format to convert from
    :type annotation_fmt_from: str
    :param annotation_fmt_to: format to convert to
    :type annotation_fmt_to: str
    :return: function
    :rtype: (str, str)  -> str | None
    """
    if annotation_fmt_from == annotation_fmt_to:
        return _move
    convert_pair = annotation_fmt_from, annotation_fmt_to
    if convert_pair == (GTF, GFF3):
        return convert_gtf_to_gff3
    elif convert_pair == (GFF3, GTF):
        return convert_gff3_to_gtf
    else:
        return None


def convert(file_path, annotation_fmt_from, annotation_fmt_to,
            working_dir=None, remove_source=True):
    """
    Convert annotation file and return path to the converted annotation file.

    :param file_path: path to decompressed file
    :type file_path: str
    :param annotation_fmt_from: annotation format constant
    :type annotation_fmt_from: str
    :param annotation_fmt_to: annotation format constant
    :type annotation_fmt_to: str
    :type working_dir: str
    :param remove_source: flag if source file should be removed. Default ``True``
    :type remove_source: bool
    :return: path to the created gtf-file
    :return: path to the converted annotation file
    :rtype: str
    """
    converter = get_converter(annotation_fmt_from, annotation_fmt_to)
    if converter is None:
        raise GenestackException('Unsupported conversion: from %s to %s' % (
            annotation_fmt_from, annotation_fmt_to))
    return converter(file_path, working_dir, remove_source=remove_source)


def convert_gff3_to_gtf(file_path, dest_folder=None, remove_source=True):
    """
    Convert annotation file and return path to the created gtf-file.

    :param file_path: path to the (possible compressed) annotation file
    :type file_path: str
    :param dest_folder: place to put file
    :type dest_folder: str
    :param remove_source: flag if source file should be removed. Default ``True``
    :type remove_source: bool
    :return: path to the created gtf-file (which is not compressed)
    :rtype: str
    """
    decompressed_file_name = decompress_file(file_path, dest_folder=dest_folder,
                                             remove_source=remove_source)

    dest_folder = dest_folder or os.curdir
    makedirs_p(dest_folder)

    base_file_name = os.path.splitext(os.path.basename(decompressed_file_name))[0]
    intermediate_files = []
    sed = local['sed']
    normalized_file_name = get_unique_name(
        os.path.join(dest_folder, os.path.basename(decompressed_file_name))
    )
    intermediate_files.append(normalized_file_name)
    # Ensemble gff3 annotation file contains ID like
    # 'gene:<gene_id>' and 'transcript:<transcript_id>'
    # Also we have to rename pseudogene to transcript
    # due https://github.com/cole-trapnell-lab/cufflinks/issues/79
    (
        sed['s/=gene:/=/', decompressed_file_name] |
        sed['s/=transcript:/=/'] |
        sed['/transcript_id=/s/pseudogene/transcript/']
     ) & RUN(stdout=normalized_file_name)
    output_file_name = get_unique_name(os.path.join(dest_folder, base_file_name + '.gtf'))
    gffread_tool = _get_gffread_tool()
    gffread_tool['-E', normalized_file_name, '-T', '-o', output_file_name] & RUN
    for name in intermediate_files:
        os.remove(name)
    if remove_source:
        for path in (file_path, decompressed_file_name):
            if os.path.exists(path):
                os.remove(path)
    return os.path.relpath(output_file_name)


def convert_gtf_to_gff3(file_path, dest_folder=None, remove_source=True):
    """
    Convert gtf to gff3, return path to the created gff3-file.

    :param file_path: path to the (possible compressed) annotation file
    :type file_path: str
    :param dest_folder: place to put file
    :type dest_folder: str
    :param remove_source: flag if source file should be removed. Default ``True``
    :type remove_source: bool
    :return: path to the created gff3-file (which is not compressed)
    :rtype: str
    """
    decompressed_file_name = decompress_file(file_path, dest_folder, remove_source=remove_source)

    dest_folder = dest_folder or os.curdir
    makedirs_p(dest_folder)

    base_file_name = os.path.splitext(os.path.basename(decompressed_file_name))[0]
    output_file_name = get_unique_name(os.path.join(dest_folder, base_file_name) + '.gff3')
    gffread_tool = _get_gffread_tool()
    # Gff read add first line as commented command that was run.
    # http://gmod.org/wiki/GFF3#GFF3_Annotation_Section:
    #     GFF3 format is a flat tab-delimited file.
    #     The first line of the file is a comment that identifies the file format and version.
    command = gffread_tool['-E', decompressed_file_name, '-o-'] | local['tail']['-n', '+2']
    command & RUN(stdout=output_file_name)
    if remove_source:
        for path in (file_path, decompressed_file_name):
            if os.path.exists(path):
                os.remove(file_path)
    return os.path.relpath(output_file_name)


def _get_gffread_tool():
    toolset = Toolset('cufflinks', CUFFLINKS_VERSION)
    return toolset.get_tool('gffread').get_tool_command()
