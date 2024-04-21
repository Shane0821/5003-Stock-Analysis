#!/bin/bash

docker compose -f spark-master-worker.yml down

docker compose -f zk-single-kafka-single.yml down

