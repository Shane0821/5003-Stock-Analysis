#!/bin/bash

sudo docker compose -f ./docker-compose/spark-master-worker.yml down

sudo docker compose -f ./docker-compose/zk-single-kafka-single.yml down

