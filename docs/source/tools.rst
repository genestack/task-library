Bioinformatics tools
====================

This page lists all the third-party resources that are accessible from any Genestack initialization script.


.. _PythonModules:

Python modules
**************

Modules required for task library itself (CPython and PyPy):

 .. include:: ../../requirements/library.pip
   :literal:

Modules that can be use from task both with CPython and PyPy

 .. include:: ../../requirements/scripts-common.pip
   :literal:

Modules that can be used in task nly for CPython
 .. include:: ../../requirements/scripts-cpython.pip
   :literal:

.. _Toolsets:

Toolsets
********

We have various bioinformatics tools installed in our system.


===================     ==============
Tool                    Versions
===================     ==============
     **Reference-based Aligners**
--------------------------------------
bowtie                  1.0.0
bowtie2                 2.0.0-beta2, 2.0.2, 2.0.6, 2.1.0, 2.2.3, 2.2.4
bsmap                   2.74
bwa                     0.6.2, 0.7.12, 0.7.5a
tophat                  2.0.10, 2.0.13, 2.0.7, 2.0.8
STAR                    2.3.0e
    **Transcriptome Assembly**
--------------------------------------
cufflinks               2.2.1
trinity                 2.0.6
detonate                1.10 1.9
rnaQUAST                0.2.1, 0.3.0_beta
rsem                    1.2.21
stringtie               1.0.4
       **FASTQ Preprocessing**
--------------------------------------
cutadapt                1.3
ea-utils                1.1.2-537
fastx_toolkit           0.0.14
fastqc                  0.11.3
seqtk                   1.0
         **Download Utilities**
--------------------------------------
aspera-connect          3.5.1.92519
GeneTorrent             3.8.6
sratoolkit              2.3.3-3
 **Bioinformatics Files Manipulation**
--------------------------------------
bcftools                1.1, 1.2
bedtools                2.17.0, 2.23.0
htslib                  1.1
picard-tools            1.106, 1.110
samtools                0.1.18, 0.1.19, 1.1, 1.2
tabix                   0.2.6
       **Variant Analysis**
--------------------------------------
vcftools                0.1.12b
snpeff                  3.4, 3.6
       **Sequence Alignment**
--------------------------------------
blat                    36
ncbi-blast              2.2.22, 2.2.31
               **Others**
--------------------------------------
augustus                3.1
bayesembler             1.2.0
cloudxdna_sRNA          1.0
ngsplot                 2.08
reaper                  13-274
===================     ==============

To use a specific tool, you need to declare it in the metainfo of the file,
in a StringValue at key ``genestack:tool.version:<tool name>``, using the version number as value.
For example, if my initialization script uses *samtools 0.1.19*, I would put the following key-value pair in its
metainfo: ``genestack:tool.version:samtools -> 0.1.19``.


