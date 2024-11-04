# Transformations
We take the harvested JSON from each source and transform this to our common data model.


### Using the transformation modules
The VICC normalizers must first be installed.

```
pip install thera-py
pip install variant-normalizer
pip install gene-normalizer
pip install disease-normalizer
```

You will then start your [local DynamoDB](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DynamoDBLocal.DownloadingAndRunning.html):
```
java -Djava.library.path=./DynamoDBLocal_lib -jar DynamoDBLocal.jar -sharedDb
```


You will then need to run the following commands for each normalizer:

[thera-py](https://github.com/cancervariants/therapy-normalization)

```
python3 -m therapy.cli --normalizer="rxnorm chemidplus ncit wikidata" --update_merged
```

[gene-normalizer](https://github.com/cancervariants/gene-normalization)
```
python3 -m gene.cli --normalizer="hgnc"
```

[disease-normalizer](https://github.com/cancervariants/disease-normalization)
```
python3 -m disease.cli --update_all --update_merged
```
