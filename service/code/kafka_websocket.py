import asyncio
from aiokafka import AIOKafkaConsumer
import websockets

class KafkaWebSocketServer:
    def __init__(self, kafka_bootstrap_servers, kafka_topics, websocket_host, websocket_port):
        self.kafka_bootstrap_servers = kafka_bootstrap_servers
        self.kafka_topics = kafka_topics
        self.websocket_host = websocket_host
        self.websocket_port = websocket_port

    async def consume_kafka(self, websocket):
        stock_data_consumer = AIOKafkaConsumer(
            self.kafka_topics[0],
            bootstrap_servers=self.kafka_bootstrap_servers
        )
        signal_consumer = AIOKafkaConsumer(
            self.kafka_topics[1],
            bootstrap_servers=self.kafka_bootstrap_servers
        )
        await stock_data_consumer.start()
        print("stock data consumer started")
        await signal_consumer.start()
        print("signal consumer started")

        async def consume_stock_data():
            async for msg in stock_data_consumer:
                print(f"Consumed stock data message: {msg.value.decode('utf-8')}")
                await websocket.send(msg.value.decode('utf-8'))

        async def consume_signal():
            async for msg in signal_consumer:
                print(f"Consumed signal message: {msg.value.decode('utf-8')}")
                await websocket.send(msg.value.decode('utf-8'))

        try:
            await asyncio.gather(
                consume_stock_data(),
                consume_signal()
            )
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            await stock_data_consumer.stop()
            await signal_consumer.stop()

    async def handle_websocket(self, websocket, path):
        await self.consume_kafka(websocket)

    def start(self):
        start_server = websockets.serve(self.handle_websocket, self.websocket_host, self.websocket_port)
        asyncio.get_event_loop().run_until_complete(start_server)
        asyncio.get_event_loop().run_forever()

kafka_bootstrap_servers = 'kafka:9092'
kafka_topics = ['real-time-stock-data-processed', 'signal-rsi-mac']
websocket_host = '0.0.0.0'
websocket_port = 8766

server = KafkaWebSocketServer(
    kafka_bootstrap_servers=kafka_bootstrap_servers,
    kafka_topics=kafka_topics,
    websocket_host=websocket_host,
    websocket_port=websocket_port)

server.start()