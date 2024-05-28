#!/bin/bash

sudo docker build --network host -f ./dockerfile/register_dockerfile -t topic-register .

sudo docker build --network host -f ./dockerfile/producer_dockerfile -t data-producer .

sudo docker build --network host -f ./dockerfile/processor_dockerfile -t streaming-processor .

sudo docker build --network host -f ./dockerfile/websocket_dockerfile -t kafka-websocket .

# TODO: use s3 and remove this
sudo docker build --network host -f ./dockerfile/k8s_spark_dockerfile -t k8s-spark .

# sudo docker tag topic-register:latest shane233/topic-register:latest
# sudo docker tag data-producer:latest shane233/data-producer:latest
# sudo docker tag reddit-producer:latest shane233/reddit-producer:latest
# sudo docker tag streaming-processor:latest shane233/streaming-processor:latest
# sudo docker tag k8s-spark:latest shane233/k8s-spark:latest
# sudo docker push shane233/topic-register:latest
# sudo docker push shane233/data-producer:latest
# sudo docker push shane233/reddit-producer:latest
# sudo docker push shane233/streaming-processor:latest
# sudo docker push shane233/k8s-spark:latest
# sudo docker rmi shane233/topic-register:latest shane233/data-producer:latest shane233/streaming-processor:latest shane233/k8s-spark:latest shane233/reddit-producer:latest