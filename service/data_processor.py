from pyspark.sql import SparkSession
from pyspark.sql.functions import *
import pyspark.sql.functions as F
from pyspark.sql.types import *

## Create a spark session
spark = SparkSession \
    .builder \
    .master('spark://172.16.0.4:7077') \
    .appName("streaming processor") \
    .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1") \
    .getOrCreate()

## Kafka configs
kafka_input_config = {
    "kafka.bootstrap.servers" : "172.16.0.3:9092",
    "subscribe" : "real-time-stock-data",
    "startingOffsets" : "latest",
    "failOnDataLoss" : "false"
}

# Define the schema for the key and value
key_schema = StructType([
    StructField("ticker_symbol", StringType()),
    # Add more fields here based on your key structure
])

value_schema = StructType([
    StructField("regular_market_price", StringType()),
    StructField("regular_market_change", StringType()),
    StructField("regular_market_change_percent", StringType()),
    StructField("regular_market_previous_close", StringType()),
    StructField("regular_market_open", StringType()),
    StructField("bid", StringType()),
    StructField("ask", StringType()),
    StructField("regular_market_volume", StringType()),
    StructField("average_volume", StringType()),
    StructField("market_cap", StringType()),
    StructField("beta", StringType()),
    StructField("pe_ratio", StringType()),
    StructField("eps", StringType()),
    StructField("1y_target_est", StringType())
    # Add more fields here based on your value structure
])

print("start")

## Read Stream
df = spark \
    .readStream \
    .format("kafka") \
    .options(**kafka_input_config) \
    .load()

# Deserialize the key and value
df = df.select(
    F.from_json(F.col("key").cast("string"), key_schema).alias("key"),
    F.from_json(F.col("value").cast("string"), value_schema).alias("value")
)

df = df.select("*") \
    .writeStream \
    .outputMode("update") \
    .format("console") \
    .trigger(continuous='10 second') \
    .start()

df.awaitTermination()

print("finish")
    