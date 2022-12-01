# A simple container for metakb-v2.

# The commands following all RUN instructions are run in a shell, which
# by default is /bin/sh -c on Linux or cmd /S /C on Windows.

# Initialize a new build stage and set the base image to the Docker
# python image that has the "latest" tag (currently 3.10.8).
FROM python

# Install pipenv and uvicorn from PyPI into the container.
RUN pip install pipenv uvicorn[standard]

# Copy the current working directory to /app in the container.
COPY . /app

# Set /app in the container to be the container's working directory for
# all RUN, CMD, ENTRYPOINT, COPY, and ADD instructions hereafter.
WORKDIR /app

# Lock all default and development packages listed in Pipfile and their
# dependencies into Pipfile.lock if the file doesn't already exist.
RUN if [ ! -f "Pipfile.lock" ] ; then pipenv lock && pipenv lock --dev ; else echo Pipfile.lock exists ; fi

# Install packages exactly as specified in Pipfile.lock into the virtual
# environment.
RUN pipenv sync

# CMD pipenv run python3 -m metakb.cli --db_url=bolt://localhost:7687 --load_latest_s3_cdms

# The container listens on port 80; TCP by default.
EXPOSE 80

# Healthchecks service up every 5m.  
HEALTHCHECK --interval=5m --timeout=3s \
    CMD curl -f http://localhost/metakb || exit 1

#
# use discover variant installation paths
# and link data paths to discovered paths
# expects volume mounts: [/app/gene/data, /app/disease/data]
#
RUN pipenv run ./discover_normalizer_paths.sh > /tmp/normalizer_paths ; \
   . /tmp/normalizer_paths ; \
   mkdir -p $SEQREPO_DATA_PATH ; \
   ln -s /app/gene/data/seqrepo/latest $SEQREPO_DATA_PATH ; \
#    mkdir -p $DISEASE_PROJECT_ROOT/data/omim ; \
#    ln -s /app/disease/data/omim/mimTitles.txt $DISEASE_PROJECT_ROOT/data/omim/omim_$(date '+%Y%m%d').tsv ;
# CMD pipenv run uvicorn metakb.main:app --port 80 --host 0.0.0.0



