Sample Initialization Scripts
=============================

Genestack initialization scripts should be written in Python.

Each script should start with a shebang specifying the Python interpreter to use.
Currently, we support

   - Python 2.7 / ``#!/usr/bin/env python2.7``
   - PyPy / ``#!/usr/bin/env pypy``

You can use either one, but bear in mind that currently our PyPy installation has fewer installed modules.
See :ref:`PythonModules`


BAM File Initialization Script
******************************

This is the script we use to initialize BAM files in Genestack:

.. code-block:: python

    #!/usr/bin/env python2.7
    # -*- coding: utf-8 -*-

    #
    # Copyright (c) 2011-2016 Genestack Limited
    # All Rights Reserved

    from genestack.bio import AlignedReads


    aligned_reads = AlignedReads()

    bam_file = aligned_reads.DOWNLOAD(AlignedReads.BAM_FILE_LOCATION,
                                      AlignedReads.BAM_EXTERNAL_URL,
                                      put_to_storage=False)[0]
    aligned_reads.put_bam_with_index(bam_file)



Let's go through it step by step.

    .. code-block:: python

        aligned_reads = AlignedReads()


As you can see, the first line creates an instance of the ``AlignedReads`` class. A Genestack file constructor called
without any parameters refers to the file that is being currently initialized. Note that if the file type does not
match the real file type of that file, an error will be raised.

    .. code-block:: python

        bam_file = aligned_reads.DOWNLOAD(AlignedReads.BAM_FILE_LOCATION,
                                      AlignedReads.BAM_EXTERNAL_URL,
                                      put_to_storage=False)[0]


Then, we call the :ref:`DOWNLOAD` method to get data from an external link.

 - ``AlignedReads.BAM_FILE_LOCATION`` is a key that is declared for the ``AlignedReads`` file type to store physical
   data. You cannot :ref:`DOWNLOAD` or :ref:`PUT` to a key that is not declared.
 - ``AlignedReads.BAM_EXTERNAL_URL`` is the key where the external link is stored.
 - ``put_to_storage`` is set to ``False`` because we will not put these files into the Genestack storage just yet.


.. code-block:: python

    aligned_reads.put_bam_with_index(bam_file)

The next step is to do some preprocessing on the BAM file before we :ref:`PUT` it to storage. More precisely, we will
sort it and index it.
Most biological files required preprocessing, but these preprocessing steps are usually already implemented in the
Tasks API; in this case, :py:meth:`~genestack.bio.AlignedReads.put_bam_with_index`.

FASTQ File Subsampling Script
*****************************

The following script shows how to subsample an input unaligned reads file (using `seqtk <https://github
.com/lh3/seqtk>`_).

.. code-block:: python

    #!/usr/bin/env python2.7
    # -*- coding: utf-8 -*-

    #
    # Copyright (c) 2011-2016 Genestack Limited
    # All Rights Reserved

    import os

    from genestack import GenestackException
    from genestack.bio import UnalignedReads
    from genestack.cla import get_argument_string, RUN, get_tool
    from genestack.compression import UNCOMPRESSED, GZIP

    if __name__ == '__main__':
        raw_reads = UnalignedReads()
        seqtk = get_tool('seqtk', 'seqtk')
        head_arguments, tail_arguments = get_argument_string().split('<in.fq>')

        source_file = raw_reads.resolve_reference(raw_reads.SOURCE_KEY, filetype=UnalignedReads)

        reads, file_format = source_file.get_reads(formats=UnalignedReads.Format.PHRED33,
                                                   spaces=[UnalignedReads.Space.BASESPACE, UnalignedReads.Space.COLORSPACE],
                                                   compressions=[UNCOMPRESSED, GZIP],
                                                   working_dir='source')

        result_reads = []
        for i, read in enumerate(reads, start=1):
            read_name = 'sub%s.fq' % i
            seqtk['sample', head_arguments.split(), read, tail_arguments.split()] & RUN(stdout=read_name)
            if not os.path.exists(read_name):
                raise GenestackException('File was not created')
            result_reads.append(read_name)
        raw_reads.put_reads(result_reads, file_format)

Then, ``genestack.cla`` module allows us to do two things:

    - retrieve a tool for ``seqtk``
    - get the file's command-line strings from its metainfo

