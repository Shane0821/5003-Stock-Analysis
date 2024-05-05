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

## Commands
Go to service directory:
```
cd service
```

To start kafka and spark cluster, execute:
```
sudo chmod +x ./start_service.sh
./start_service.sh
```

To stop kafka and spark cluster, execute:
```
sudo chmod +x ./stop_service.sh
./stop_service.sh
```

After starting kafka and spark, execute:
```
python3 ./code/register_topic.py
python3 ./code/data_producer.py

python3 ./code/kafka_ws_producer.py
python3 ./code/kafka_websocket.py
```
This will start scrapers which send data to kafka.

Finally, we start spark streaming to process data and send it to db, kafka, console, etc. Create a new terminal and execute:
```
sudo docker exec -it spark-master /bin/bash -c "pip install py4j && python3 /tmp/code/streaming_processor.py"
```
