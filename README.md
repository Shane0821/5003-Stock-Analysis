# 5003-Project

## Requirement
- docker desktop installed

## Commands
To start kafka and spark cluster, execute:
```
./start_service.sh
```

To stop kafka and spark cluster, execute:
```
./stop_service.sh
```

After starting kafka and spark, execute:
```
python3 register_topic.py
python3 data_producer.py
```
This will start scrapers which send data to kafka.

Finally, we start spark streaming to process data and send it to db/front end:
```
sudo docker exec -it spark-master pip install py4j && python3 ./data_processor.py
```