#!/bin/bash

sudo docker build --network host -f ./dockerfile/register_dockerfile -t topic-register .

sudo docker build --network host -f ./dockerfile/producer_dockerfile -t data-producer .