from kafka import KafkaProducer
from kafka.errors import KafkaError
import json
from scraper import Scraper

producer = KafkaProducer(
    client_id='real-time-stock-producer-1',
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('ascii'),
    key_serializer=lambda v: v.encode('ascii'),
    api_version = (0, 10, 1)
)

raw_data = {'price': 100, 'name': 'AMZN'}

for i in range(10):
    print("before")
    producer.send('real-time-stock', key='AMZN', value=raw_data)
    producer.flush()
    print("sent")

# scraper_AMZN = Scraper('AMZN')
# scraper_GOOG = Scraper('GOOG')
# scraper_AAPL = Scraper('AAPL')

# scraper_AMZN.start()
# scraper_GOOG.start()
# scraper_AAPL.start() 


