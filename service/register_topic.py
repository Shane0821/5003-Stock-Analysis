from kafka.admin import KafkaAdminClient, NewTopic

admin = KafkaAdminClient(
    bootstrap_servers='172.16.0.3:9092',
    client_id='admin',
)

try:
    topic = NewTopic(name='real-time-stock-data', num_partitions=3, replication_factor=1)
    admin.create_topics([topic], timeout_ms=3000)

    topic = NewTopic(name='real-time-stock-data-processed', num_partitions=3, replication_factor=1)
    admin.create_topics([topic], timeout_ms=3000)
except Exception as e:
    print(e)

admin.close()