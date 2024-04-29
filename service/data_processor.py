from pyspark.sql import SparkSession
from pyspark.sql.functions import *
import pyspark.sql.functions as F
from pyspark.sql.types import *

## Create a spark session
spark = SparkSession \
    .builder \
    .master('spark://172.16.0.4:7077') \
    .appName("streaming processor") \
    .config("spark.jars.packages", "org.mongodb.spark:mongo-spark-connector_2.12:10.2.1,org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.3") \
    .config("spark.sql.streaming.checkpointLocation", "/tmp/spark/checkpoint") \
    .getOrCreate()

def load_data():
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
    ## Read Stream
    dfStream = spark \
        .readStream \
        .format("kafka") \
        .options(**kafka_input_config) \
        .load()

    # Deserialize the key and value, flatten the key and value
    df = dfStream.select(
        F.from_json(F.col("key").cast("string"), key_schema).alias("key"),
        F.from_json(F.col("value").cast("string"), value_schema).alias("value"),
        "timestamp"
    ).select("timestamp", "key.*", "value.*")
    return df


def preprocess(df):
    # Preprocess the data
    df = df.withColumn('regular_market_price', regexp_replace(col('regular_market_price'), ',', '').cast(FloatType()))
    df = df.withColumn('regular_market_change', col('regular_market_change').cast(FloatType()))
    df = df.withColumn('regular_market_change_percent', regexp_replace(col('regular_market_change_percent'), '[%()]', '').cast(FloatType()))

    df = df.withColumn('regular_market_previous_close', regexp_replace(col('regular_market_previous_close'), ',', '').cast(FloatType()))
    df = df.withColumn('regular_market_open', regexp_replace(col('regular_market_open'), ',', '').cast(FloatType()))

    df = df.withColumn('bid', regexp_replace(col('bid'), ',', ''))
    df = df.withColumn('bid_split', when(col('bid') == '--', array(lit('0'), lit('0'))).otherwise(split(col('bid'), ' x ')))
    df = df.withColumn('bid_price', df['bid_split'].getItem(0).cast('float'))
    df = df.withColumn('bid_size', df['bid_split'].getItem(1).cast('int'))
    df = df.drop('bid_split')
    df = df.drop('bid')

    df = df.withColumn('ask', regexp_replace(col('ask'), ',', ''))
    df = df.withColumn('ask_split', when(col('ask') == '--', array(lit('0'), lit('0'))).otherwise(split(col('ask'), ' x ')))
    df = df.withColumn('ask_price', df['ask_split'].getItem(0).cast('float'))
    df = df.withColumn('ask_size', df['ask_split'].getItem(1).cast('int'))
    df = df.drop('ask_split')
    df = df.drop('ask')

    df = df.withColumn('regular_market_volume', regexp_replace(col('regular_market_volume'), ',', '').cast(LongType()))
    df = df.withColumn('average_volume', regexp_replace(col('average_volume'), ',', '').cast(LongType()))

    df = df.withColumn('last_char', substring(col('market_cap'), -1, 1))
    df = df.withColumn('market_cap', regexp_replace(col('market_cap'), '[,KMBT]', '').cast(FloatType()))
    df = df.withColumn('market_cap_type', 
                    when(col('last_char') == 'K', 1)
                    .when(col('last_char') == 'M', 2)
                    .when(col('last_char') == 'B', 3)
                    .when(col('last_char') == 'T', 4)
                    .otherwise(0))
    df = df.drop('last_char')

    df = df.withColumn('beta', regexp_replace(col('beta'), '--', '0').cast(FloatType()))
    df = df.withColumn('pe_ratio', regexp_replace(col('pe_ratio'), '--', '0').cast(FloatType()))
    df = df.withColumn('eps', regexp_replace(col('eps'), '--', '0').cast(FloatType()))
    df = df.withColumn('1y_target_est', when(col('1y_target_est') == '--', 0). \
                            otherwise(regexp_replace(col('1y_target_est'), ',', '')).cast(FloatType()))
    return df


def gen_signal(stock_data, ma_len, process_interval, ma_threshold_perc=0.01, rsi_threshold=70):
    stock_data = stock_data.withColumn('timestamp', date_trunc('second', col('timestamp')))

    stock_data = stock_data.groupBy(
            'ticker_symbol',
            window('timestamp', f'{ma_len} seconds', f'{process_interval} seconds')
        ) \
        .agg(
            last('regular_market_price').alias('regular_market_price'),
            avg('regular_market_price').alias('moving_avg_price'),
            max('regular_market_price').alias('max_price'),
            min('regular_market_price').alias('min_price'),
            last('timestamp').alias('timestamp'),
            col('window').getField('start').alias('start'),
            col('window').getField('end').alias('end'),
        )

    stock_data = stock_data.filter(col('end') <= current_timestamp())

    stock_data = stock_data.withColumn(
            'mean_reversion_signal',
            when((col('regular_market_price') - col('moving_avg_price')) / col('moving_avg_price') > ma_threshold_perc, 1)
            .when((col('regular_market_price') - col('moving_avg_price')) / col('moving_avg_price') < -ma_threshold_perc, -1)
            .otherwise(0)
        )

    stock_data = stock_data.withColumn(
        'rsi_signal',
        when(100 - (100 / (1 + ((col('max_price') - col('moving_avg_price')) / (col('moving_avg_price') - col('min_price'))))) > rsi_threshold, -1)
        .when(100 - (100 / (1 + ((col('max_price') - col('moving_avg_price')) / (col('moving_avg_price') - col('min_price'))))) < 100 - rsi_threshold, 1)
        .otherwise(0)
    )

    return stock_data.select('ticker_symbol', col('end').alias('timestamp'), 'moving_avg_price', 'mean_reversion_signal', 'rsi_signal')


def write_to_console(df, interval, mode='update'):
    # Write to console
    dfStream = df.writeStream \
        .outputMode(mode) \
        .format("console") \
        .trigger(processingTime=interval) \
        .start()

    dfStream.awaitTermination()


def write_to_mongo(df, interval, database, collection, mode='complete'):
    # Write to MongoDB
    dfStream = df.writeStream \
    .outputMode(mode) \
    .format("mongodb") \
    .option("spark.mongodb.connection.uri", "mongodb+srv://msbd:bdt5003!@5003-cluster-2.mongocluster.cosmos.azure.com/?tls=true&authMechanism=SCRAM-SHA-256&retrywrites=false&maxIdleTimeMS=120000") \
    .option("spark.mongodb.database", database) \
    .option("spark.mongodb.collection", collection) \
    .trigger(processingTime=interval) \
    .start()

    dfStream.awaitTermination()


print("start")

stock_data = preprocess(load_data())

ma_len = 300
process_interval = 5
data_with_signal = gen_signal(stock_data, ma_len, process_interval)

write_to_console(data_with_signal, f'{process_interval} seconds', 'update')

print("end")