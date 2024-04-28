import asyncio
from aiokafka import AIOKafkaConsumer
import websockets

class KafkaWebSocketServer:
    def __init__(self, kafka_bootstrap_servers, kafka_topic, websocket_host, websocket_port):
        self.kafka_bootstrap_servers = kafka_bootstrap_servers
        self.kafka_topic = kafka_topic
        self.websocket_host = websocket_host
        self.websocket_port = websocket_port

    async def consume_kafka(self, websocket):
        consumer = AIOKafkaConsumer(
            self.kafka_topic,
            bootstrap_servers=self.kafka_bootstrap_servers,
            loop=asyncio.get_event_loop()
        )
        await consumer.start()

        print("consumer started")

        try:
            async for msg in consumer:
                print(f"Consumed message: {msg.value.decode('utf-8')}")
                await websocket.send(msg.value.decode('utf-8'))
        finally:
            await consumer.stop()

    async def handle_websocket(self, websocket, path):
        await self.consume_kafka(websocket)

    def start(self):
        start_server = websockets.serve(self.handle_websocket, self.websocket_host, self.websocket_port)
        asyncio.get_event_loop().run_until_complete(start_server)
        asyncio.get_event_loop().run_forever()

kafka_bootstrap_servers = '172.16.0.3:9092'
kafka_topic = 'ws_stock_data'
websocket_host = 'localhost'
websocket_port = 8766

server = KafkaWebSocketServer(
    kafka_bootstrap_servers=kafka_bootstrap_servers,
    kafka_topic=kafka_topic,
    websocket_host=websocket_host,
    websocket_port=websocket_port)
server.start()