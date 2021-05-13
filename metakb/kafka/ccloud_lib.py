"""A module to parse in confluent kafka parameters and configurations"""
import argparse
import sys
from confluent_kafka import KafkaError
from confluent_kafka.admin import AdminClient
from confluent_kafka.admin import NewTopic
from uuid import uuid4

# import certifi


class Delta(object):
    """Meta-KB Delta stores the deserialized JSON record for the Kafka key."""

    def __init__(self, _meta=None, assertions=None, genes=None,
                 variants=None, sources=None, evidence=None):
        """Initialize the Delta class

        :param dict _meta: delta _meta data
        :param dict assertions: delta assertion data
        :param dict genes: delta gene data
        :param dict sources: delta source data
        :param dict evidence: delta evidence data
        """
        self._meta = _meta
        self.assertions = assertions
        self.genes = genes
        self.variants = variants
        self.sources = sources
        self.evidence = evidence
        # Unique id used to track produce request success/failures.
        self.id = uuid4()

    @staticmethod
    def to_dict(delta, ctx):
        """Return dictionary to be serialized"""
        return dict(_meta=delta._meta, assertions=delta.assertions,
                    genes=delta.genes, variants=delta.variants,
                    sources=delta.sources, evidence=delta.evidence)

    @staticmethod
    def from_dict(obj, ctx):
        """Return object to Delta instance"""
        if obj is None:
            return None

        return Delta(_meta=obj['_meta'], assertions=obj['assertions'],
                     genes=obj['genes'], variants=obj['variants'],
                     sources=obj['sources'], evidence=obj['evidence'])


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Confluent Python Client \
                                     example to produce messages \
                                     to Confluent Cloud")
    parser._action_groups.pop()
    required = parser.add_argument_group('required arguments')
    required.add_argument('-f',
                          dest="config_file",
                          help="path to Confluent Cloud configuration file",
                          required=True)
    required.add_argument('-t',
                          dest="topic",
                          help="topic name",
                          required=True)
    required.add_argument('-s',
                          dest="schema_registry",
                          help="Schema Registry (http(s)://host[:port]",
                          required=True)
    required.add_argument('-r',
                          dest="resource",
                          help="Knowledgebase resource name",
                          required=False)

    args = parser.parse_args()

    return args


def read_ccloud_config(config_file):
    """Read Confluent Cloud configuration for librdkafka clients

    :param file config_file: file contains confluent cloud configuration
    """
    conf = {}
    with open(config_file) as fh:
        for line in fh:
            line = line.strip()
            if len(line) != 0 and line[0] != "#":
                parameter, value = line.strip().split('=', 1)
                conf[parameter] = value.strip()

    # conf['ssl.ca.location'] = certifi.where()
    return conf


def pop_schema_registry_params_from_config(conf):
    """Remove potential Schema Registry related configurations"""
    conf.pop('schema.registry.url', None)
    conf.pop('basic.auth.user.info', None)
    conf.pop('basic.auth.credentials.source', None)

    return conf


def create_topic(conf, topic):
    """Create a topic if needed"""
    admin_client_conf = pop_schema_registry_params_from_config(conf.copy())
    a = AdminClient(admin_client_conf)

    fs = a.create_topics([NewTopic(topic,
                                   num_partitions=1,
                                   replication_factor=3)])
    for topic, f in fs.items():
        try:
            f.result()  # The result itself is None
            print("Topic {} created".format(topic))
        except Exception as e:
            # Continue if error code TOPIC_ALREADY_EXISTS, which may be true
            # Otherwise fail fast
            if e.args[0].code() != KafkaError.TOPIC_ALREADY_EXISTS:
                print("Failed to create topic {}: {}".format(topic, e))
                sys.exit(1)
