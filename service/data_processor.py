from kafka import KafkaConsumer
from kafka.errors import KafkaError
from kafka.admin import KafkaAdminClient, NewTopic
import json
import threading

admin = KafkaAdminClient(
    bootstrap_servers='localhost:29092',
    client_id='admin',
)

try:
    topic = NewTopic(name='real-time-stock-data', num_partitions=3, replication_factor=1)
    admin.create_topics([topic], timeout_ms=3000)
except Exception as e:
    print(e)

admin.close()

print(topic.name)

comsumer1 = KafkaConsumer(
    topic.name,
    client_id='real-time-stock-consumer-1',
    group_id='real-time-stock-group',
    bootstrap_servers='localhost:29092',
    value_deserializer=lambda v: json.loads(v.decode('ascii')),
    key_deserializer=lambda v: json.loads(v.decode('ascii')),
)

comsumer2 = KafkaConsumer(
    topic.name,
    client_id='real-time-stock-consumer-2',
    group_id='real-time-stock-group',
    bootstrap_servers='localhost:29092',
    value_deserializer=lambda v: json.loads(v.decode('ascii')),
    key_deserializer=lambda v: json.loads(v.decode('ascii')),
)

def print_message(consumer, cid):
    for message in consumer:
        print(message.partition, message.offset, message.key, message.value, cid)

thread1 = threading.Thread(target=print_message, args=(comsumer1, 1, ))
thread2 = threading.Thread(target=print_message, args=(comsumer2, 2, ))

thread1.start()
thread2.start()

thread1.join()
thread2.join()