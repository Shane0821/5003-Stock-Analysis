#!/bin/bash

docker compose -f zk-single-kafka-single.yml up -d

docker compose -f spark-master-worker.yml up -d