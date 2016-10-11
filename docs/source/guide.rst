Guides
######

The typical logic of a Genestack initialization script goes like this:

 - get data to working directory
 - process data
 - put data to storage

Let us go through each of these steps in more detail.

Retrieving data
***************

.. _DOWNLOAD:

DOWNLOAD: Retrieving external files
-----------------------------------

If you need to get data from external storage (i.e. a remote FTP or website), you will need to download the data
using the :py:meth:`~genestack.File.DOWNLOAD` method.
The ``DOWNLOAD`` method retrieves the file(s) specified in an :py:class:`~genestack.metainfo.ExternalLink` in the
source file's metainfo and copies it to the task's working directory.
The file will also be put into Genestack storage by default.

The following types of external links are currently supported in :py:meth:`~genestack.File.DOWNLOAD`,
all files should be in public access, except raw files, which should be accessible by file owner:

 - HTTP (``http://`` or ``https://``)
 - FTP (``ftp://``)
 - Aspera links (``ascp://``) see `Aspera Transfer Guide <http://www.ncbi.nlm.nih.gov/books/NBK242625/>`_ for more details
 - Amazon files (``s3://``) format of links are same as used in `AWS Command Line Interface <https://aws.amazon.com/cli/?nc1=h_ls>`_.
   This will work faster then link to same file via http
 - Raw genestack files (``raw:``) key there file reference to Raw file is stored


.. _GET:

GET: Retrieving from Genestack storage
--------------------------------------

:py:meth:`~genestack.File.GET` fetches data from the Genestack storage and puts it in the task directory.
Most biological file types already have helper methods to get data; therefore, it is preferable to use these helper
methods as much as possible, and not use :py:meth:`~genestack.File.GET` explicitly in you code.

Sending data to storage
***********************

.. _PUT:

PUT: putting data to storage
----------------------------

You can store files into the Genestack storage, using the :py:meth:`~genestack.File.PUT` method.
Note that you can only ``PUT`` data into a metainfo key that is declared authorized to store data for the
corresponding file type.
Most biological file types already have helper methods to get data; therefore, it is preferable to use these helper
methods as much as possible, and not use :py:meth:`~genestack.File.PUT` explicitly in you code.

Storing a file's index
----------------------

Save data to special index storage.

Storing key-value data
----------------------

File types that inherit from ``StringMapFile``, such as ``ApplicationPageFile``, have a special key-value storage
which can be accessed using an API similar to that of Java's ``Map`` interface.
The main methods are :py:meth:`~genestack.StringMapFile.put` and :py:meth:`~genestack.StringMapFile.get`.
See :py:class:`~genestack.StringMapFile` for the complete list of methods.


Executing shell commands
************************

Plumbum
-------

To execute shell commands from initialization scripts, we use the `plumbum <https://plumbum.readthedocs
.io/en/latest/>`_ library.

Genestack gives you access to a wide range of :ref:`pre-installed bioinformatics
third-party tools <Toolsets>`. For each tool that you use, you must specify the tool and its version in
the file's metainfo before initialization.

The method :py:meth:`~genestack.cla.get_tool`
returns a plumbum `LocalCommand <https://plumbum.readthedocs.io/en/latest/local_commands.html#guide-local-commands>`_
object.

You can use
`pipes <https://plumbum.readthedocs.io/en/latest/local_commands.html#guide-local-commands-pipelining>`_
(``|``) and
`redirects <https://plumbum.readthedocs.io/en/latest/local_commands.html#guide-local-commands-redir>`_
(``>``) to combine commands.

There are several ways of executing commands.

    - Using Genestack execution modifiers
        These modifiers write a start and end marks to the task logs.

        - :py:attr:`~genestack.cla.RUN` runs a command in the foreground (same as :py:attr:`plumbum.FG`),
          you can use the ``stdout`` argument if you need to redirect the result to a file.
        - :py:attr:`~genestack.cla.OUTPUT` collects command stdout to a variable (like `__call__()`)

          .. code-block:: python

                samtools = get_tool('samtools', 'samtools')
                header = samtools['view', '-H'] & OUTPUT

        This is the preferred way of executing commands.

    - Using `plumbum execution modifiers <http://plumbum.readthedocs.io/en/latest/_modules/plumbum/commands/modifiers.html/>`_

    - Using parentheses:

        .. code-block:: python

            samtools = get_tool('samtools', 'samtools')
            header = samtools['view', '-H']()

.. warning:: This will return the ``stdout`` output of the command as a string. Do not use it if the output can
             contain a lot of data.

If the tool you're using requires to have some other tools available,
you can add it with the ``uses=[...]`` argument to :py:meth:`~genestack.cla.get_tool`

.. code-block:: python

    tophat_tool = get_tool('tophat', 'tophat', uses=['bowtie2', 'samtools'])


Example
-------

Let's assume we want to execute the following shell command from an initialization task:

.. code-block:: sh

    `seqtk/1.0/seqtk sample -s100 test.fastq.gz 50000 > subsample_of_test.fastq.gz`

This is what we would write in Python:

.. code-block:: python

   from genestack.cla import get_tool, RUN

   seqtk = get_tool('seqtk', 'seqtk')
   seqtk['sample' '-s100', 'test.fastq.gz', 50000] & RUN(stdout='subsample_of_test.fastq.gz')


- `get_tool` returns a command that contains the ``seqtk`` executable from the ``seqtk`` toolset.
- ``seqtk['sample', 'sample' '-s100', 'test.fastq.gz', 50000]`` returns a command with arguments
- ``& RUN(stdout='subsample_of_test.fastq.gz')`` runs the command and redirects its output to a file.


You can get the directory of a third-party tool using :py:meth:`~genestack.cla.get_tool_path`


.. warning:: It is not possible to access two different versions of the same tool in one script.


.. warning:: You can still use the ``subprocess`` module to execute shell commands.
   To do this, you can get the path to the executable with :py:meth:`~genestack.cla.get_tool_path`.
   Be careful while passing file names to ``subprocess`` calls with ``shell=True``,
   files will be stored with their original names and "ambiguous" characters like ``&`` and ``>``
   will need to be properly escaped.

