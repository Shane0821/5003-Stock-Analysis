from kafka import KafkaProducer
from kafka.errors import KafkaError
import json
from scraper import Scraper

topic = 'real-time-stock-data'

producer = KafkaProducer(
    client_id='real-time-stock-producer-1',
    bootstrap_servers='localhost:29092',
    value_serializer=lambda v: json.dumps(v).encode('ascii'),
    key_serializer=lambda v: json.dumps(v).encode('ascii'),
)

raw_data = {'price': 100, 'name': 'AMZN'}
for i in range(10):
    print("before")
    producer.send(topic, key={'id': 0}, value=raw_data)
    producer.send(topic, key={'id': 1}, value=raw_data)
    producer.send(topic, key={'id': 2}, value=raw_data)
    producer.send(topic, key={'id': 3}, value=raw_data)
    producer.send(topic, key={'id': 4}, value=raw_data)
    print("sent")

producer.flush()
# scraper_AMZN = Scraper('AMZN')
# scraper_GOOG = Scraper('GOOG')
# scraper_AAPL = Scraper('AAPL')

# scraper_AMZN.start()
# scraper_GOOG.start()
# scraper_AAPL.start() 


