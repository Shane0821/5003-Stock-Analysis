# 5003-Project
MSBD 5003 Group Project.

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
    volumes:
      - ./code:/tmp/code

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
<!-- python3 ./service/code/kafka_ws_producer.py -->
python3 ./code/kafka_websocket.py
```

### Local Deployment
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

**Note**: remember to rebuild images after chaning the code.

### Deploy on K8s
#### Deploy Zookeeper
```
kubectl apply -f deployment/zookeeper.yaml
```
You can check if the deployment is successful by running:
```
kubectl get services -o wide
kubectl get pod -o wide
```

#### Deploy Kafka
```
kubectl apply -f deployment/kafka.yaml
kubectl get pod -o wide
```
Wait until kafka pod is ready (READY 0/1 -> READY 1/1).

#### Register Topics
```
kubectl apply -f deployment/register-topic.yaml
```
Pod register-topic-...'s status should change from running to completed in a few seconds.
Execute this to check if the topics are successfully registered. If yes, you should see all the registered topics.

```
kubectl exec <kafka-pod-name>  -- /bin/bash -c "kafka-topics --bootstrap-server localhost:9092 --list"
```
Finally, delete the topic register job using:
```
kubectl delete -f deployment/register-topic.yaml
```

To test kafka service locally, you should expose an external ip. You can skip this if you are using cloud services.
```
minikube tunnel
```
Then test with kafkacat. 
```
echo "hello world!" | kafkacat -P -b localhost:9092 -t test
kafkacat -C -b localhost:9092 -t test
```
The command should execute without errors, indicating that producers are communicating fine with kafka in k8s.

**Note**: If you are using cloud services, replace localhost with external ipv4 address. Remember to convert hostname to ipv4 address. Don't forget to add "external-ip  kafka" to /etc/hosts on the client host. 

#### Deploy Producer
```
kubectl apply -f deployment/producer.yaml
```

#### Deploy Spark Cluster for Processing Streaming Data
Before starting this service, you should set ```spark.executor.instances, spark.kubernetes.cores, spark.kubernetes.memory``` based on you demand in ```deployment/spark.yaml```.

```
kubectl apply -f deployment/spark.yaml
```

Keep track of the output of spark driver using ```kubectl logs -f <pod-name>```.

**Note**: when terminating the spark service, you have to delete spark driver manually using ```kubectl delete pods <pod-name>```.

#### Deploy Websocket
```
kubectl apply -f deployment/websocket.yaml
```
