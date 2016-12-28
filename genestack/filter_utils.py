# -*- coding: utf-8 -*-

import itertools
import time

from genestack.utils import opener, log_info


def get_filtered_file_name(src_file_name):
    suffix = '.filtered'
    return (src_file_name[:-3] if src_file_name.endswith('.gz') else src_file_name) + suffix


def writefq(read, fh):
    data = [
        '@', read['id'], ' ', read['comment'], '\n',
        read['seq'], '\n',
        '+\n',
        read['qual'], '\n'
    ]
    fh.write(''.join(data))


def readfq(file_path):
    """
    Yields a records of fastq or fasta input file.

    :param file_path: path to the source file
    :type file_path: str
    """
    last = None  # this is a buffer keeping the last unprocessed line
    while True:  # mimic closure; is it a bad idea?
        if not last:  # the first record or a record following a fastq
            for line in file_path:  # search for the start of the next record
                if line[0] in '>@':  # fasta/q header line
                    last = line[:-1]  # save this line
                    break
        if not last: break
        partition = last[1:].partition(' ')
        name, comment, seqs, last = partition[0], partition[2], [], None
        for line in file_path:  # read the sequence
            if line[0] in '@+>':
                last = line[:-1]
                break
            seqs.append(line[:-1])
        if not last or last[0] != '+': # this is a fasta record
            # yield a fasta record
            yield {
                'id': name,
                'comment': comment,
                'seq': ''.join(seqs),
                'qual': None
            }
            if not last: break
        else:  # this is a fastq record
            seq, leng, seqs = ''.join(seqs), 0, []
            for line in file_path:  # read the quality
                seqs.append(line[:-1])
                leng += len(line) - 1
                if leng >= len(seq):  # have read enough quality
                    last = None
                    # yield a fastq record
                    yield {
                        'id': name,
                        'comment': comment,
                        'seq': seq,
                        'qual': ''.join(seqs)
                    }
                    break
            if last:  # reach EOF before reading enough quality
                # yield a fasta record instead
                yield {
                    'id': name,
                    'comment': comment,
                    'seq': seq,
                    'qual': None
                }
                break


def leave_only_paired(src_file_0, src_file_1, filtered_file_0, filtered_file_1):
    """
    Returns paths of two files with records from ``src_file_0`` and ``src_file_1``,
    respectively, present in both ``filtered_file_0`` and ``filtered_file_1``.

    All source files must be FASTQ.
    src_file_* are the files, from which filtered_file_* are produced.

    :type src_file_0: str
    :type src_file_1: str
    :type filtered_file_0: str
    :type filtered_file_1: str
    :rtype: list[str]
    """
    log_info('Start discarding unpaired reads')

    paired_reads_left = 0
    dst_file_0 = filtered_file_0 + '.only_paired'
    dst_file_1 = filtered_file_1 + '.only_paired'
    with opener(filtered_file_0) as filtered_0, opener(filtered_file_1) as filtered_1, \
            opener(src_file_0) as src_0, opener(dst_file_0, 'w') as dst_0, \
            opener(src_file_1) as src_1, opener(dst_file_1, 'w') as dst_1:
        src_records_0 = readfq(src_0)
        src_records_1 = readfq(src_1)
        filtered_records_0 = readfq(filtered_0)
        filtered_records_1 = readfq(filtered_1)

        try:
            filtered_record_0 = filtered_records_0.next()
            filtered_record_1 = filtered_records_1.next()
        except StopIteration:
            log_info('No paired reads left in the result.')
            return [dst_file_0, dst_file_1]

        count = 0
        start = time.time()
        for (src_record_0, src_record_1) in itertools.izip(src_records_0, src_records_1):
            count += 1
            if count % 10000 == 0:
                log_info('Processed %d reads in %.2f s' % (count, time.time() - start))
            try:
                if filtered_record_0['id'] == src_record_0['id'] and filtered_record_1['id'] == src_record_1['id']:
                    writefq(filtered_record_0, dst_0)
                    writefq(filtered_record_1, dst_1)

                    paired_reads_left += 1

                    filtered_record_0 = filtered_records_0.next()
                    filtered_record_1 = filtered_records_1.next()
                elif filtered_record_0['id'] == src_record_0['id']:
                    filtered_record_0 = filtered_records_0.next()
                elif filtered_record_1['id'] == src_record_1['id']:
                    filtered_record_1 = filtered_records_1.next()
            except StopIteration:
                continue
    log_info('total: %d\nleft: %d' % (count, paired_reads_left))
    return [dst_file_0, dst_file_1]
