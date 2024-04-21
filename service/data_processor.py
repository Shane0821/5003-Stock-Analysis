from pyspark.sql import SparkSession
from pyspark.sql.functions import *
import pyspark.sql.functions as F
from pyspark.sql.types import *

## Create a spark session
spark = SparkSession \
    .builder \
    .master('spark://localhost:7077') \
    .appName("streaming processor") \
    .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1") \
    .getOrCreate()

## Kafka configs
kafka_input_config = {
    "kafka.bootstrap.servers" : "localhost:29092",
    "subscribe" : "real-time-stock-data",
    "startingOffsets" : "latest",
    "failOnDataLoss" : "false"
}

print("start")

## Read Stream
df = spark \
    .readStream \
    .format("kafka") \
    .options(**kafka_input_config) \
    .load() \
    .selectExpr("CAST(key AS STRING)", "CAST(value AS STRING)") \
    .writeStream \
    .outputMode("update") \
    .format("console") \
    .trigger(continuous='2 second') \
    .start()

df.awaitTermination()

print("finish")
    