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

def send_data(ticker_symbol, data):
    producer.send(topic, key={'ticker_symbol': ticker_symbol}, value=data)

scraper_AMZN = Scraper('AMZN', on_data=send_data)
scraper_GOOG = Scraper('GOOG', on_data=send_data)
scraper_AAPL = Scraper('AAPL', on_data=send_data)

scraper_AMZN.start()
scraper_GOOG.start()
scraper_AAPL.start() 


