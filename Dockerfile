# A simple container for metakb-service.
# Runs service on port 80.
# Healthchecks service up every 5m.  

FROM python:3.7
RUN apt update ; apt install -y rsync
RUN pip install pipenv uvicorn[standard]
COPY . /app
WORKDIR /app
RUN if [ ! -f "Pipfile.lock" ] ; then pipenv lock ; else echo Pipfile.lock exists ; fi
RUN pipenv sync
EXPOSE 80
HEALTHCHECK --interval=5m --timeout=3s \
    CMD curl -f http://localhost/metakb || exit 1

#
# use discover variant installation paths
# and link data paths to discovered paths
# expects volume mounts: [/app/gene/data, /app/disease/data]
#
RUN pipenv run \
    ./discover_normalizer_paths.sh > /tmp/normalizer_paths ; \
    . /tmp/normalizer_paths ; \
    mkdir -p $VARIANT_PROJECT_ROOT/data/seqrepo ; \
    ln -s /app/gene/data/seqrepo/latest $SEQREPO_DATA_PATH ; \
    mkdir -p $DISEASE_PROJECT_ROOT/data/omim ; \
    ln -s /app/disease/data/omim/mimTitles.txt $DISEASE_PROJECT_ROOT/data/omim/omim_$(date '+%Y%m%d').tsv ;
CMD pipenv run uvicorn metakb.main:app --port 80 --host 0.0.0.0



