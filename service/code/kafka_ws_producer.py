# for testing only

from kafka import KafkaProducer
import time
import json

topic = 'ws_stock_data'

producer = KafkaProducer(
    client_id='websocket_data_producer',
    bootstrap_servers='kafka:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
    key_serializer=lambda v: json.dumps(v).encode('utf-8'),
)

def send_data(ticker_symbol, data):
    producer.send(topic, key={'ticker_symbol': ticker_symbol}, value=data)

# thread1: send data for every second
while True:
    print("sending data")
    # send_data('AAPL', 'AAPL data')
    # send_data('GOOGL', 'GOOGL data')
    # send_data('AMZN', 'AMZN data')
    send_data('TSLA', 'TSLA data')
    time.sleep(1)


