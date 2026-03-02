# This file is for generating an image of the neo4j dump
FROM neo4j:5

COPY neo4j.dump /dump/neo4j.dump

RUN neo4j-admin database load neo4j \
    --from-path=/dump \
    --overwrite-destination=true
