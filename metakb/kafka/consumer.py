"""A module for comsuming confluent kafka message"""
from confluent_kafka import DeserializingConsumer
from confluent_kafka.schema_registry.json_schema import JSONDeserializer
from confluent_kafka.serialization import StringDeserializer, \
    SerializationError

from metakb import PROJECT_ROOT
import ccloud_lib
import json


delta_dir = PROJECT_ROOT / 'data'
schema_dir = PROJECT_ROOT / 'metakb' / 'kafka' / 'schema.json'


class Consumer():
    """A Kafka class to consume delta message"""

    args = ccloud_lib.parse_args()
    config_file = args.config_file
    topic = args.topic
    conf = ccloud_lib.read_ccloud_config(config_file)

    with open(schema_dir, 'r') as f1:
        schema_str = json.dumps(json.load(f1))
    json_deserializer = JSONDeserializer(schema_str,
                                         from_dict=ccloud_lib.Delta.from_dict)
    string_deserializer = StringDeserializer('utf_8')

    consumer_conf = ccloud_lib.pop_schema_registry_params_from_config(conf)
    consumer_conf['key.deserializer'] = string_deserializer
    consumer_conf['value.deserializer'] = json_deserializer
    consumer_conf['group.id'] = 'meta_kb delta group 1'
    consumer_conf['auto.offset.reset'] = 'earliest'

    consumer = DeserializingConsumer(consumer_conf)
    consumer.subscribe([topic])

    while True:
        try:
            # SIGINT can't be handled when polling, limit timeout to 1 second.
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            elif msg.error():
                print('error: {}'.format(msg.error()))
            else:
                delta = msg.value()
                if delta is not None:
                    print(f"Consumed record with key_id {msg.key()}")
                    for key in delta.__dict__.keys():
                        print(f"{key}: {delta.__dict__[key]} \n")
        except KeyboardInterrupt:
            break
        except SerializationError as e:
            # Report malformed record, discard results, continue polling
            print("Message deserialization failed {}".format(e))
            pass

    consumer.close()
