# bin - command line wrappers

## Styleguide:

* The runner will execute any command line program from the project ROOT directory.  Each command line program MUST assume CWD is the project root.

* Each command line program MUST write its final output to one of the dvc controlled directories [downloads, outputs]

* All command line programs MUST be executed in context of a dvc pipeline.  All outputs and dependencies MUST be part of a pipeline.  see pipelines/README.md

* Each command line program SHOULD execute tests/integration/<my tests>
