from kafka import KafkaProducer
from kafka.errors import KafkaError
import json
from scraper import Scraper

topic = 'real-time-stock-data'

producer = KafkaProducer(
    client_id='real-time-stock-producer-1',
    bootstrap_servers='172.16.0.3:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
    key_serializer=lambda v: json.dumps(v).encode('utf-8'),
)

def send_data(ticker_symbol, data):
    producer.send(topic, key={'ticker_symbol': ticker_symbol}, value=data)

# scraper_AMZN = Scraper('AMZN', on_data=send_data)
# scraper_GOOG = Scraper('GOOG', on_data=send_data)
scraper_AAPL = Scraper('AAPL', on_data=send_data)

# scraper_AMZN.start()
# scraper_GOOG.start()
scraper_AAPL.start()


