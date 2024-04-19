from kafka import KafkaConsumer
from kafka.errors import KafkaError
import json

comsumer = KafkaConsumer(
    'real-time-stock', # topic
    client_id='real-time-stock-consumer-1',
    group_id='real-time-stock-group',
    bootstrap_servers=['localhost:9092'],
    value_deserializer=lambda v: json.loads(v.decode('ascii')),
    key_deserializer=lambda v: v.decode('ascii'),
    api_version = (0, 10, 1)
)

print(comsumer.subscription())

for message in comsumer:
    print(message)