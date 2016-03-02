API Reference
#############

This is the complete API reference of the Genestack Task Library.

.. toctree::
   :maxdepth: 2

.. _CoreModules:

File Types
**********

.. _CoreFiles:

Core File Types
---------------

ApplicationPageFile
+++++++++++++++++++
.. autoclass:: genestack.ApplicationPageFile
        :members:
        :show-inheritance:

AuxiliaryFile
+++++++++++++
.. autoclass:: genestack.AuxiliaryFile
        :members:
        :show-inheritance:

ExternalDatabase
++++++++++++++++
.. autoclass:: genestack.ExternalDatabase
        :members:
        :show-inheritance:

File
++++
.. autoclass:: genestack.File
        :members:
        :show-inheritance:

IndexFile
+++++++++
.. autoclass:: genestack.IndexFile
        :members:
        :show-inheritance:

RawFile
+++++++

.. autoclass:: genestack.RawFile
        :members:
        :show-inheritance:

ReportFile
++++++++++
.. autoclass:: genestack.ReportFile
        :members:
        :show-inheritance:

StringMapFile
+++++++++++++
.. autoclass:: genestack.StringMapFile
        :members:
        :show-inheritance:


.. _BioFiles:

Biological File Types
---------------------

AlignedReads
++++++++++++
.. autoclass:: genestack.bio.AlignedReads
        :members:
        :show-inheritance:

        .. autoattribute:: genestack.bio.AlignedReads.BAM_FILE_LOCATION
        .. autoattribute:: genestack.bio.AlignedReads.BAMINDEX_FILE_LOCATION

BED
+++
.. autoclass:: genestack.bio.BED
        :members:
        :show-inheritance:

        .. autoattribute:: genestack.bio.BED.DATA_LOCATION

CodonTable
++++++++++
.. autoclass:: genestack.bio.CodonTable
        :members:
        :show-inheritance:

        .. autoattribute:: genestack.bio.CodonTable.DATA_LOCATION

Experiment
++++++++++
.. autoclass:: genestack.bio.Experiment
        :members:
        :show-inheritance:

ExternalDatabase
++++++++++++++++
.. autoclass:: genestack.bio.ExternalDatabase
        :members:
        :show-inheritance:

GenomeAnnotation
++++++++++++++++
.. autoclass:: genestack.bio.GenomeAnnotation
        :members:
        :show-inheritance:

        .. autoattribute:: genestack.bio.GenomeAnnotation.ANNOTATION_LOCATION

MappedReadsCounts
+++++++++++++++++
.. autoclass:: genestack.bio.MappedReadsCounts
        :members:
        :show-inheritance:

        .. autoattribute:: genestack.bio.MappedReadsCounts.DATA_LOCATION

MicroarrayAssay
+++++++++++++++
.. autoclass:: genestack.bio.MicroarrayAssay
        :members:
        :show-inheritance:

        .. autoattribute:: genestack.bio.MicroarrayAssay.DATA_LOCATION

ReferenceGenome
+++++++++++++++
.. autoclass:: genestack.bio.ReferenceGenome
        :members:
        :show-inheritance:

        .. autoattribute:: genestack.bio.ReferenceGenome.SEQUENCE_LOCATION
        .. autoattribute:: genestack.bio.ReferenceGenome.ANNOTATIONS_LOCATION

UnalignedReads
++++++++++++++
.. autoclass:: genestack.bio.UnalignedReads
        :members:
        :show-inheritance:

        .. autoattribute:: genestack.bio.UnalignedReads.READS_LOCATION

Variation
+++++++++
.. autoclass:: genestack.bio.Variation
        :members:
        :show-inheritance:

        .. autoattribute:: genestack.bio.Variation.DATA_LOCATION

WIG
+++
.. autoclass:: genestack.bio.WIG
        :members:
        :show-inheritance:

        . autoattribute:: genestack.bio.WIG.WIG_SOURCE_LOCATION

Exceptions
**********

.. autoclass:: genestack.GenestackException
        :members:
        :show-inheritance:


Command Line Applications
*************************

.. autoclass:: genestack.CLA
        :members:
        :show-inheritance:

.. autoclass:: genestack.Toolset
        :members:
        :show-inheritance:

.. autoclass:: genestack.Tool
        :members:
        :show-inheritance:


Metainfo
********

.. autoclass:: genestack.metainfo.Metainfo
        :members:
        :show-inheritance:


.. autoclass:: genestack.metainfo.MetainfoValue
        :members:

.. autoclass:: genestack.metainfo.MetainfoSimpleValue
        :members:
        :show-inheritance:

.. autoclass:: genestack.metainfo.BooleanValue
        :members:
        :show-inheritance:

.. autoclass:: genestack.metainfo.DateTimeValue
        :members:
        :show-inheritance:

.. autoclass:: genestack.metainfo.StringValue
        :members:
        :show-inheritance:

.. autoclass:: genestack.metainfo.IntegerValue
        :members:
        :show-inheritance:

.. autoclass:: genestack.metainfo.DecimalValue
        :members:
        :show-inheritance:

.. autoclass:: genestack.metainfo.MemorySizeValue
        :members:
        :show-inheritance:

.. autoclass:: genestack.metainfo.ExternalLink
        :members:
        :show-inheritance:

.. autoclass:: genestack.metainfo.OrganizationValue
        :members:
        :show-inheritance:

.. autoclass:: genestack.metainfo.PersonValue
        :members:
        :show-inheritance:

.. autoclass:: genestack.metainfo.PublicationValue
        :members:
        :show-inheritance:

.. autoclass:: genestack.metainfo.PhysicalValue
        :members:
        :show-inheritance:

.. autoclass:: genestack.metainfo.FileReference
        :members:
        :show-inheritance:


Others
******

.. autoclass:: genestack.StorageUnit
        :members:
        :show-inheritance:

.. autoclass:: genestack.Indexer
        :members:
        :show-inheritance:

.. autoclass:: genestack.bio.VariationIndexer
        :members:
        :show-inheritance:

.. autoclass:: genestack.bio.GenomeInterval
        :members:
        :show-inheritance:

.. autoclass:: genestack.bio.GenomeQuery
        :members:
        :show-inheritance:

.. autoclass:: genestack.bio.ReferenceGenomeIndexer
        :members:
        :show-inheritance:

.. autoclass:: genestack.bio.BEDIndexer
        :members:
        :show-inheritance:

.. autoclass:: genestack.bio.WIGIndexer
        :members:
        :show-inheritance:

.. automodule:: genestack.compression
    :members:

.. automodule:: genestack.utils
    :members:
