from kafka import KafkaConsumer
from kafka.errors import KafkaError
from kafka.admin import KafkaAdminClient, NewTopic
import json

topic = 'real-time-stock-data'

comsumer = KafkaConsumer(
    topic,
    group_id='real-time-stock-group',
    bootstrap_servers='localhost:29092',
    value_deserializer=lambda v: json.loads(v.decode('ascii')),
    key_deserializer=lambda v: json.loads(v.decode('ascii')),
)

print(comsumer.partitions_for_topic(topic))

for message in comsumer:
    print(message.partition, message.offset, message.key, message.value)
