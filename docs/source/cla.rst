Command line API
################

Plumbum
^^^^^^^

To execute commandlines we use `plumbum <https://plumbum.readthedocs.io/en/latest/>`_ library.


Genestack gives you access to installed biotools. See list of avaliable :ref:`Toolsets`.


To do it you need to specify toolset version in file metainfo before initialization.


:py:meth:`~genestack.cla.get_tool`
returns `Local command <https://plumbum.readthedocs.io/en/latest/local_commands.html#guide-local-commands>`_
You can use
`pipes <https://plumbum.readthedocs.io/en/latest/local_commands.html#guide-local-commands-pipelining>`_
(``|``) and
`redirects <https://plumbum.readthedocs.io/en/latest/local_commands.html#guide-local-commands-redir>`_
(``>``) to combine commands.


There is several ways of executing this commands.

    - Use Genestack execution modifiers.
        This modifiers write start and end marks to logs.

        - :py:attr:`~genestack.cla.RUN` runs command in foreground (same as :py:attr:`plumbum.FG`),
          you can use ``stdout`` argument of run if you need redirect result to file.
        - :py:attr:`~genestack.cla.OUTPUT` collects command stdout to variable (same as use of `__call__()` on command)

          .. code-block:: python

                samtools = get_tool('samtools', 'samtools')
                header = samtools['view', '-H'] & OUTPUT

        This is preferred way of executing commands.
    - Use `plumbum execution modifiers <http://plumbum.readthedocs.io/en/latest/_modules/plumbum/commands/modifiers.html/>`_
    - Use parenthesis:

        .. code-block:: python

            samtools = get_tool('samtools', 'samtools')
            header = samtools['view', '-H']()

.. warning:: This will return stdout of command as string, dont use it if output can have a lot of data.


If your tool requires to have some other toolsets in command path
you can add it with ``uses=[...]`` argument to :py:meth`~genestack.cla.get_tool`

.. code-block:: python

    tophat_tool = get_tool('tophat', 'tophat', uses=['bowtie2', 'samtools'])


Example
^^^^^^^

To execute this command in shell form task

.. code-block:: sh

    `seqtk/1.0/seqtk sample -s100 test.fastq.gz 50000 > subsample_of_test.fastq.gz`

we need to do next:

.. code-block:: python

   from genestack.cla import get_tool, RUN

   seqtk = get_tool('seqtk', 'seqtk')
   seqtk['sample' '-s100', 'test.fastq.gz', 50000] & RUN(stdout='subsample_of_test.fastq.gz')


- `get_tool` return command that contains ``seqtk`` executable from ``seqtk`` toolset.
- ``seqtk['sample', 'sample' '-s100', 'test.fastq.gz', 50000]`` return command filled with arguments
- ``& RUN(stdout='subsample_of_test.fastq.gz')`` run command and redirects in stdout to file.


You can get directory of toolset using :py:meth:`~genestack.cla.get_tool_path`


.. warning:: It is not possible to access two different versions of the one toolset in script.


.. warning:: You can still use subprocess module,
   to do this you can get executable with :py:meth:`~genestack.cla.get_tool_path`
   Be careful with passing file names to subprocess with ``shell=True``,
   files stored with theirs original names and need to be proper escaped.

