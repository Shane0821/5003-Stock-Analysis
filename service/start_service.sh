#!/bin/bash

sudo docker compose -f ./docker-compose/zk-single-kafka-single.yml up -d

sudo docker compose -f ./docker-compose/spark-master-worker.yml up -d