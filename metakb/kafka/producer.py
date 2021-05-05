"""A module for confluent kafka"""
from confluent_kafka import SerializingProducer
from confluent_kafka.serialization import StringSerializer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.json_schema import JSONSerializer

import ccloud_lib
from uuid import uuid4
from datetime import date
from metakb import PROJECT_ROOT
import json
import logging


logger = logging.getLogger('metakb')
logger.setLevel(logging.DEBUG)


delivered_records = 0
today = date.today().strftime('%Y%m%d')
delta_dir = PROJECT_ROOT / 'data'
schema_dir = PROJECT_ROOT / 'metakb' / 'kafka' / 'schema.json'


class Kafka():
    """A Kafka class to produce delta message"""

    args = ccloud_lib.parse_args()
    config_file = args.config_file
    topic = args.topic
    conf = ccloud_lib.read_ccloud_config(config_file)

    # Create topic if needed
    ccloud_lib.create_topic(conf, topic)

    schema_registry_conf = {
        'url': conf['schema.registry.url'],
        'basic.auth.user.info': conf['basic.auth.user.info']}

    with open(schema_dir, 'r') as f1:
        schema_str = json.dumps(json.load(f1))
    schema_registry_client = SchemaRegistryClient(schema_registry_conf)
    json_serializer = JSONSerializer(schema_str,
                                     schema_registry_client,
                                     ccloud_lib.Delta.to_dict)

    # Create Producer instance
    producer_conf = ccloud_lib.pop_schema_registry_params_from_config(conf)
    producer_conf['key.serializer'] = StringSerializer('utf_8')
    producer_conf['value.serializer'] = json_serializer
    producer = SerializingProducer(producer_conf)

    # Optional per-message on_delivery handler (triggered by poll() or flush())
    # when a message has been successfully delivered or
    # permanently failed delivery (after retries).
    def acked(err, msg):
        """Delivery report handler called on
        successful or failed delivery of message
        """
        global delivered_records

        if err is not None:
            print("Failed to deliver message: {}".format(err))
        else:
            delivered_records += 1
            print(f"Produced record to topic {msg.topic()} "
                  f"partition [{msg.partition()}] @ offset {msg.offset()}")

    resource = args.resource
    delta_dir = delta_dir / f"{resource}" / f'{resource}_deltas_{today}.json'
    with open(delta_dir, 'r') as f2:
        delta_data = json.load(f2)

    print(f"Producing delta for {resource}...")
    delta = ccloud_lib.Delta(_meta=delta_data['_meta'],
                             assertions=delta_data['assertions'],
                             variants=delta_data['variants'],
                             sources=delta_data['sources'])
    producer.produce(topic, key=str(uuid4()), value=delta, on_delivery=acked)
    # p.poll() serves delivery reports (on_delivery)
    # from previous produce() calls.
    producer.poll(0)

    producer.flush()

    print(f"{delivered_records} messages were produced to topic {topic}!")

# a = Kafka()
