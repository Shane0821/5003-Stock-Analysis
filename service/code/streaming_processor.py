from pyspark.sql import SparkSession
from pyspark.sql.functions import *
import pyspark.sql.functions as F
from pyspark.sql.types import *
from pyspark.ml.regression import LinearRegression
from pyspark.ml.feature import VectorAssembler
from pyspark.sql.window import Window
from shutil import rmtree

## Create a spark session
spark = SparkSession \
    .builder \
    .appName("streaming processor") \
    .config("spark.jars.packages", "org.mongodb.spark:mongo-spark-connector_2.12:10.2.1,org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.1") \
    .config("spark.sql.streaming.checkpointLocation", "/tmp/spark/checkpoint") \
    .getOrCreate()

spark.sparkContext.setLogLevel("ERROR")

def load_data():
    ## Kafka configs
    kafka_input_config = {
        "kafka.bootstrap.servers" : "kafka:9092",
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


def gen_signal(stock_data, ma_len, process_interval, ma_threshold_perc=0.03, rsi_threshold=70):
    stock_data = stock_data.withColumn('timestamp', date_trunc('second', col('timestamp')))

    stock_data = stock_data.withWatermark('timestamp', f'1 second').groupBy(
            'ticker_symbol',
            window('timestamp', f'{ma_len} seconds', f'{process_interval} seconds')
        ) \
        .agg(
            last('regular_market_price').alias('regular_market_price'),
            avg('regular_market_price').alias('moving_avg_price'),
            max('regular_market_price').alias('max_price'),
            min('regular_market_price').alias('min_price'),
            last('timestamp').alias('timestamp'),
            col('window').getField('end').alias('end'),
        )

    stock_data = stock_data.filter(col('end') <= current_timestamp())

    # mean reversion signal
    stock_data = stock_data.withColumn(
            'mac_signal',
            when((col('regular_market_price') - col('moving_avg_price')) / col('moving_avg_price') > ma_threshold_perc, -1)
            .when((col('regular_market_price') - col('moving_avg_price')) / col('moving_avg_price') < -ma_threshold_perc, 1)
            .otherwise(0)
        )

    stock_data = stock_data.withColumn('rsi', 100 - (100 / (1 + ((col('regular_market_price') - col('min_price')) / (col('max_price') - col('regular_market_price'))))))

    # RSI signal
    stock_data = stock_data.withColumn(
        'rsi_signal',
        when(col('rsi') > rsi_threshold, -1)
        .when(col('rsi') < 100 - rsi_threshold, 1)
        .otherwise(0)
    )

    return stock_data.select('ticker_symbol', col('end').alias('timestamp'), 'regular_market_price', 'moving_avg_price', 'rsi', 'mac_signal', 'rsi_signal')


def write_to_console(df, interval, mode='complete'):
    # Write to console
    dfStream = df.writeStream \
        .outputMode(mode) \
        .format("console") \
        .trigger(processingTime=interval) \
        .option("truncate", "false") \
        .start()

    return dfStream


def write_to_mongo(df, database, collection, interval, mode='complete'):
    # Write to MongoDB
    dfStream = df.writeStream \
    .outputMode(mode) \
    .format("mongodb") \
    .option("spark.mongodb.connection.uri", "mongodb+srv://msbd:bdt5003!@5003-cluster-2.mongocluster.cosmos.azure.com/?tls=true&authMechanism=SCRAM-SHA-256&retrywrites=false&maxIdleTimeMS=120000") \
    .option("spark.mongodb.database", database) \
    .option("spark.mongodb.collection", collection) \
    .trigger(processingTime=interval) \
    .start()

    return dfStream


def write_to_kafka(df, topic, interval, mode='complete'):
    # Write to Kafka
    if (topic == 'real-time-stock-data-processed'):
        # Define the schema for the key and value
        key_schema = StructType([
            StructField("ticker_symbol", StringType()),
            # Add more fields here based on your key structure
        ])

        value_schema = StructType([
            StructField("regular_market_price", FloatType()),
            StructField("regular_market_change", FloatType()),
            StructField("regular_market_change_percent", FloatType()),
            StructField("regular_market_previous_close", FloatType()),
            StructField("regular_market_open", FloatType()),
            StructField("bid_price", FloatType()),
            StructField("bid_size", IntegerType()),
            StructField("ask_price", FloatType()),
            StructField("ask_size", IntegerType()),
            StructField("regular_market_volume", LongType()),
            StructField("average_volume", LongType()),
            StructField("market_cap", FloatType()),
            StructField("market_cap_type", IntegerType()),
            StructField("beta", FloatType()),
            StructField("pe_ratio", FloatType()),
            StructField("eps", FloatType()),
            StructField("1y_target_est", FloatType()),
            StructField("timestamp", TimestampType())
            # Add more fields here based on your value structure
        ])

        df = df.select(
            F.to_json(F.struct([F.col(field.name) for field in value_schema])).alias("value"),
            F.to_json(F.struct([F.col(field.name) for field in key_schema])).alias("key")
        )
    
    elif (topic == 'signal-rsi-mac'):
        # Define the schema for the key and value
        key_schema = StructType([
            StructField("ticker_symbol", StringType()),
            # Add more fields here based on your key structure
        ])

        value_schema = StructType([
            StructField("timestamp", TimestampType()),
            StructField("moving_avg_price", FloatType()),
            StructField("rsi", FloatType()),
            StructField("mac_signal", IntegerType()),
            StructField("rsi_signal", IntegerType())
            # Add more fields here based on your value structure
        ])

        df = df.select(
            F.to_json(F.struct([F.col(field.name) for field in value_schema])).alias("value"),
            F.to_json(F.struct([F.col(field.name) for field in key_schema])).alias("key")
        )


    dfStream = df.writeStream \
        .outputMode(mode) \
        .format("kafka") \
        .option("kafka.bootstrap.servers", "kafka:9092") \
        .option("topic", topic) \
        .trigger(processingTime=interval) \
        .start()
    
    return dfStream


model = None
database = "stock"
process_interval = 3
signal_gen_interval = 10
ma_len = 300
training_interval = 180

def train_model(batch_df, batch_id):
    global model
    # Check if DataFrame is empty
    windowSpec = Window.partitionBy('ticker_symbol').orderBy('timestamp')
    batch_df = batch_df.withColumn("label", lag("regular_market_price", 10).over(windowSpec))

    # Filter out rows with null labels
    batch_df = batch_df.filter(batch_df.label.isNotNull())

    batch_df.persist()

    # Check if DataFrame is empty
    if (len(batch_df.take(1)) == 0):
        batch_df.unpersist()
        return

    print("training...")

    columns = ['regular_market_price', 'regular_market_change', 'regular_market_change_percent', 'regular_market_previous_close', 'regular_market_open', 'bid_price', 'bid_size', 'ask_price', 'ask_size', 'market_cap', 'market_cap_type', 'beta', 'pe_ratio', 'eps', '1y_target_est']
    assembler = VectorAssembler(inputCols=columns, outputCol='features')

    batch_df = assembler.transform(batch_df)
    batch_df = batch_df.select('features', 'label')

    lr = LinearRegression(maxIter=100, regParam=0.1, elasticNetParam=0.8, featuresCol='features', labelCol='label')

    model = lr.fit(batch_df)

    batch_df.unpersist()
    
    print("finish training")

    print(model.coefficients)
    print(model.intercept)


def OLS(df, batch_id):
    global model

    if (model is None):
        return
    
    df = df.groupBy('ticker_symbol').agg(
        last('regular_market_price').alias('regular_market_price'),
        last('regular_market_change').alias('regular_market_change'),
        last('regular_market_change_percent').alias('regular_market_change_percent'),
        avg('regular_market_previous_close').alias('regular_market_previous_close'),
        avg('regular_market_open').alias('regular_market_open'),
        avg('bid_price').alias('bid_price'),
        avg('bid_size').alias('bid_size'),
        avg('ask_price').alias('ask_price'),
        avg('ask_size').alias('ask_size'),
        avg('market_cap').alias('market_cap'),
        avg('market_cap_type').alias('market_cap_type'),
        avg('beta').alias('beta'),
        avg('pe_ratio').alias('pe_ratio'),
        avg('eps').alias('eps'),
        avg('1y_target_est').alias('1y_target_est')
    )

    columns = ['regular_market_price', 'regular_market_change', 'regular_market_change_percent', 'regular_market_previous_close', 'regular_market_open', 'bid_price', 'bid_size', 'ask_price', 'ask_size', 'market_cap', 'market_cap_type', 'beta', 'pe_ratio', 'eps', '1y_target_est']
    assembler = VectorAssembler(inputCols=columns, outputCol='features')
    
    df = assembler.transform(df)
    df = model.transform(df)

    df = df.withColumn('ratio', col('prediction') / col('regular_market_price'))

    df = df.withColumn('ols_signal', when(col('ratio') > 1.03, 1).when(col('ratio') < 0.97, -1).otherwise(0))

    df = df.select('ticker_symbol', current_timestamp().alias('timestamp'), 'regular_market_price', 'prediction', 'ratio', 'ols_signal')


    df.persist()

    # write to kafka

    # Define the schema for the key and value
    key_schema = StructType([
        StructField("ticker_symbol", StringType()),
        # Add more fields here based on your key structure
    ])

    value_schema = StructType([
        StructField("timestamp", TimestampType()),
        StructField("regular_market_price", FloatType()),
        StructField("prediction", FloatType()),
        StructField("ratio", FloatType()),
        StructField("ols_signal", IntegerType())
        # Add more fields here based on your value structure
    ])

    kakfa = df.select(
        F.to_json(F.struct([F.col(field.name) for field in value_schema])).alias("value"),
        F.to_json(F.struct([F.col(field.name) for field in key_schema])).alias("key")
    )

    kakfa.write.format("kafka").mode("append") \
    .option("kafka.bootstrap.servers", "kafka:9092") \
    .option("topic", "signal-ols") \
    .save()

    # write to mongodb
    df.write.format("mongodb").mode("append")\
    .option("spark.mongodb.connection.uri", "mongodb+srv://msbd:bdt5003!@5003-cluster-2.mongocluster.cosmos.azure.com/?tls=true&authMechanism=SCRAM-SHA-256&retrywrites=false&maxIdleTimeMS=120000") \
    .option("spark.mongodb.database", database) \
    .option("spark.mongodb.collection", "signal-ols") \
    .save()

    df.unpersist()


print("start")

stock_data = preprocess(load_data())

training_stream = stock_data.writeStream \
    .foreachBatch(train_model) \
    .trigger(processingTime=f'{training_interval} seconds') \
    .start()

prediction_stream = stock_data.writeStream \
    .foreachBatch(OLS) \
    .trigger(processingTime=f'{signal_gen_interval} seconds') \
    .start()

real_time_stock_data_processed_mongo_stream = write_to_mongo(stock_data, database, "real-time-stock-data", f'{process_interval} seconds', 'append')
real_time_stock_data_processed_kafka_stream = write_to_kafka(stock_data, "real-time-stock-data-processed", f'{process_interval} seconds', 'append')

data_with_signal = gen_signal(stock_data, ma_len, signal_gen_interval)

signal_mongo_stream = write_to_mongo(data_with_signal, database, 'signal-rsi-mac', f'{signal_gen_interval} seconds', 'append')
signal_kafka_stream = write_to_kafka(data_with_signal, "signal-rsi-mac", f'{signal_gen_interval} seconds', 'append')
# signal_console_stream = write_to_console(data_with_signal, f'{signal_gen_interval} seconds', 'append')


############################################

training_stream.awaitTermination()
prediction_stream.awaitTermination()

real_time_stock_data_processed_mongo_stream.awaitTermination()
real_time_stock_data_processed_kafka_stream.awaitTermination()

signal_mongo_stream.awaitTermination()
signal_kafka_stream.awaitTermination()
# signal_console_stream.awaitTermination()

print("end")