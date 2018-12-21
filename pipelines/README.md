

# Generate a stage file from a given command and execute the command.

## Example


## Create sentinel and run a command, telling DVC what files to version

```
# add a sentinel file
dvc add downloads/civic/sentinel.txt

# create a pipeline step, stored in pipelines/ dir
# note: All commands assime CWD is in root dir _and_ we want to save in subdir
# So, we set -c `Directory within your project to run your command and place stage file in.`
dvc run --file downloads.civic.json.dvc --overwrite-dvcfile \
  -d ../downloads/civic/sentinel.txt \
  -o ../downloads/civic/civic.json.gz \
  -c pipelines \
  --ignore-build-cache \
  'cd .. ; bin/download_civic.sh'  
```

## Outputs are saved in cache as hashes

```
$ tree .dvc/cache
.dvc/cache
├── 68
│   └── 08ca805661622ad65ae014a4b2a094
└── eb
    └── a8a9559f47692dc4206560d40a40de
```

## After running, validate we can reproduced the stage

```
$ dvc repro pipelines/downloads.civic.json.dvc
Stage 'downloads/civic/sentinel.txt.dvc' didn't change.
Stage 'pipelines/downloads.civic.json.dvc' didn't change.
Pipeline is up to date. Nothing to reproduce.
```

## Push the results to the bucket

```
dvc push

$ aws s3 ls --recursive  s3://metakb-dvc
2018-12-21 12:14:18          4 68/08ca805661622ad65ae014a4b2a094
2018-12-21 12:14:18    1719784 eb/a8a9559f47692dc4206560d40a40de
2018-12-20 11:05:39       5843 index.html

```
