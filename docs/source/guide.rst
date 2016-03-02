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
