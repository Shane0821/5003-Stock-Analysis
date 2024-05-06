# 5003-Project

## Requirement
- google chrome
  ```
  sudo apt-get install google-chrome-stable 
  ```
- docker desktop
- python (3.9+), with:
    - kafka-python
    - selenium
    - webdriver_manager
    ```
    pip install kafka-python selenium webdriver_manager

    pip install asyncio aiokafka websockets
    ```

## How to Use
### Test locally
#### Requirements
- OS: linux
- Docker desktop
- Google chrome
  ```
  sudo apt-get install google-chrome-stable 
  ```
- python (3.11.9), with
  - kafka-python
  - selenium
  - webdriver_manager
  - asyncio
  - aiokafka
  - websockets
    ```
    pip install kafka-python selenium webdriver_manager

    pip install asyncio aiokafka websockets
    ```
#### Commands
Go to service directory:
```
cd service
```

Start kafka and spark with the following docker-compose.yml file:
```
version: '3'

networks:
  app-network:
    ipam:
      driver: default
      config:
        - subnet: 172.16.0.0/24

services:
  zookeeper:
    image: confluentinc/cp-zookeeper:7.6.1
    networks:
      app-network:
        ipv4_address: 172.16.0.2
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
      ZOOKEEPER_TICK_TIME: 2000
    ports:
      - '2181:2181'

  kafka:
    image: confluentinc/cp-kafka:7.6.1
    depends_on:
      - zookeeper
    networks:
      app-network:
        ipv4_address: 172.16.0.3
    ports:
      - '9092:9092'
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://172.16.0.3:9092
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT
      KAFKA_INTER_BROKER_LISTENER_NAME: PLAINTEXT
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
    healthcheck:
      test: kafka-topics --bootstrap-server localhost:9092 --list
      interval: 30s
      timeout: 10s
      retries: 5

  spark-master:
    image: bitnami/spark:3.4.3
    networks:
      app-network:
        ipv4_address: 172.16.0.4
    container_name: spark-master
    ports:
      - "8080:8080"
      - "7077:7077"
    environment:
      - "SPARK_MODE=master"

  spark-worker-1:
    image: bitnami/spark:3.4.3
    networks:
      app-network:
        ipv4_address: 172.16.0.5
    container_name: spark-worker-1
    depends_on:
      - spark-master
    ports:
      - "8081:8081"
    environment:
      - "SPARK_MODE=worker"

  spark-worker-2:
    image: bitnami/spark:3.4.3
    networks:
      app-network:
        ipv4_address: 172.16.0.6
    container_name: spark-worker-2
    depends_on:
      - spark-master
    ports:
      - "8082:8081"
    environment:
      - "SPARK_MODE=worker"
```

After starting kafka and spark, execute:
```
python3 ./code/register_topic.py
python3 ./code/data_producer.py
```
This will start scrapers which send data to kafka.

Finally, we start spark streaming to process data and send it to db, kafka, console, etc. Create a new terminal and execute:
```
sudo docker exec -it spark-master /bin/bash -c "pip install py4j && python3 /tmp/code/streaming_processor.py"
```

To start websocket, run:
```
python3 ./code/kafka_ws_producer.py
python3 ./code/kafka_websocket.py
```

### Deployment
#### Requirements
- OS: linux
- Docker desktop installed.

#### Commands
Go to service directory:
```
cd service
```

Build images for topic registry, data producer and streaming processor:
```
sudo chmod +x ./build_images.sh
./build_images.sh
```

To start all the services, execute:
```
sudo chmod +x ./start_service.sh
./start_service.sh
```

To track the output of streaming processor, run:
```
sudo docker logs --follow spark-streaming-processor
```

To stop all the services, execute:
```
sudo chmod +x ./stop_service.sh
./stop_service.sh
```