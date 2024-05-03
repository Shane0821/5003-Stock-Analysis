from pyspark.sql import SparkSession
from pyspark.sql.functions import *
import pyspark.sql.functions as F
from pyspark.sql.types import *
from pyspark.sql.window import Window
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.regression import LinearRegression

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
    df = df = df.withColumn('1y_target_est', when(col('1y_target_est') == '--', 0). \
                            otherwise(regexp_replace(col('1y_target_est'), ',', '')).cast(FloatType()))
    return df

def aggregate_stock_data(agg, aggregate_interval, water_mark_window, moving_average_window,):
    if aggregate_interval != 'second':
        # Aggregate by aggregate_stock_data
        agg = agg.withColumn('timestamp', date_trunc(aggregate_interval, col('timestamp')))

    agg = agg.withWatermark('timestamp', water_mark_window) \
        .groupBy('ticker_symbol',
                 window(col("timestamp"), moving_average_window),
                 'regular_market_price'
                 ).agg(
            max('regular_market_price').alias('whigh'),
            min('regular_market_price').alias('wlow'),
            first('regular_market_price').alias('wopen'),
            last('regular_market_price').alias('wclose'),
            avg("regular_market_price").alias('w_moving_average'),
            (last('regular_market_volume') - first('regular_market_volume')).alias('wvolume_change'),
            
            last('regular_market_previous_close').alias('regular_market_previous_close'),
            last('regular_market_open').alias('regular_market_open'),
            last('bid_price').alias('bid_price'),
            last('bid_size').alias('bid_size'),
            last('ask_price').alias('ask_price'),
            last('ask_size').alias('ask_size'),
            last('average_volume').alias('average_volume'),
            last('market_cap').alias('market_cap'),
            last('market_cap_type').alias('market_cap_type'),
            last('beta').alias('beta'),
            last('pe_ratio').alias('pe_ratio'),
            last('eps').alias('eps'),
            last('1y_target_est').alias('1y_target_est')
        )
    return agg

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


def mean_reversion_strategy(df_with_watermark, ma_threshold_perc):
    # Create the mean reversion signal column
    agg = df_with_watermark.withColumn(
        'mean_reversion_signal',
        when((col('wclose') - col('w_moving_average')) / col('w_moving_average') > ma_threshold_perc, 1)
        .when((col('wclose') - col('w_moving_average')) / col('w_moving_average') < -ma_threshold_perc, -1)
        .otherwise(0)
    )
    return agg

def get_rsi_signal(agg):
    # Calculate gain and loss within each window
    agg = agg.withColumn("gain", col("whigh") - col("wlow"))
    agg = agg.withColumn("loss", col("wlow") - col("whigh"))

    # Calculate the duration of each window in seconds
    agg = agg.withColumn(
        "window_duration",
        (unix_timestamp(col("window").end) - unix_timestamp(col("window").start))
    )

    # Calculate average gain and loss using the duration in seconds
    agg = agg.withColumn(
        "avg_gain",
        col("gain") / when(col("window_duration") > 0, col("window_duration")).otherwise(1)
    ).withColumn(
        "avg_loss",
        col("loss") / when(col("window_duration") > 0, col("window_duration")).otherwise(1)
    )

    # Compute RSI
    agg = agg.withColumn(
        "rsi",
        100 - (100 / (1 + (col("avg_gain") / col("avg_loss"))))
    )

    agg = agg.withColumn(
        "rsi_signal",
        when(col("rsi") > 70, -1)
        .when(col("rsi") < 30, 1)
        .otherwise(0)
    )
    agg = agg.drop("gain","loss",'avg_gain','avg_loss')
    return agg

def ols_strategy(df):
    # 假设 df 已经是一个 Spark DataFrame，并已加载数据
    # 计算日收益率
    df = df.withColumn('returns', log(col('regular_market_price') / lag(col('regular_market_price'), 1).over(Window.orderBy("timestamp"))))
    df = df.na.drop()

    # 计算方向
    df = df.withColumn('direction', signum(col('returns')).cast('int'))

    # 生成滞后特征
    lags = 2
    cols = []
    for lag in range(1, lags + 1):
        col_name = f'lag_{lag}'
        df = df.withColumn(col_name, lag(col('returns'), lag).over(Window.orderBy("timestamp")))
        cols.append(col_name)
    df = df.na.drop()

    # 向量化特征用于线性回归
    vectorAssembler = VectorAssembler(inputCols=cols, outputCol="features")
    df = vectorAssembler.transform(df)

    # 线性回归模型
    lr = LinearRegression(featuresCol='features', labelCol='returns')

    # 模型训练和预测（pos_ols_1）
    model_1 = lr.fit(df)
    df = model_1.transform(df).withColumn('pos_ols_1', signum(col('prediction')).cast('int')).drop('prediction')

    # 更改labelCol为'direction'进行训练和预测（pos_ols_2）
    lr.setLabelCol('direction')
    model_2 = lr.fit(df)
    df = model_2.transform(df).withColumn('pos_ols_2', signum(col('prediction')).cast('int')).drop('prediction')

    # 计算策略收益
    df = df.withColumn('strat_ols_1', col('pos_ols_1') * col('returns'))
    df = df.withColumn('strat_ols_2', col('pos_ols_2') * col('returns'))

    # 计算仓位变动
    df = df.withColumn('positions_ols_1', col('pos_ols_1') - lag(col('pos_ols_1'), 1).over(Window.orderBy("timestamp")))
    df = df.withColumn('positions_ols_2', col('pos_ols_2') - lag(col('pos_ols_2'), 1).over(Window.orderBy("timestamp")))

    # 计算累计收益
    df = df.withColumn('cum_returns', exp(sum(col('returns')).over(Window.orderBy("timestamp"))))
    df = df.withColumn('cum_strat_ols_1', exp(sum(col('strat_ols_1')).over(Window.orderBy("timestamp"))))
    df = df.withColumn('cum_strat_ols_2', exp(sum(col('strat_ols_2')).over(Window.orderBy("timestamp"))))
    return df

print("*"*50 + "\n"+ "Start data preprocessing")
# basic data frequency: per 5 seconds
stock_data = preprocess(load_data())
#print('-'*50 + '\nData Input:')
print('='*50 + '\nStart to create ols signal:')
data_signal = ols_strategy(stock_data)
write_to_console(data_signal, '30 second', mode='update')

# user input
#window = '60 minute' # 60 data poin
print("="*50 + "\n"+ "Start data aggregation")
aggregate_interval = 'second'
water_mark_window = '20 second'
moving_average_window = '10 second'
aggregate_data = aggregate_stock_data(stock_data, aggregate_interval, water_mark_window, moving_average_window)



#print('='*50 + '\nStart to create mean-reversion signal:')
#ma_threshold_perc = 0.01
#data_signal = mean_reversion_strategy(aggregate_data, ma_threshold_perc)

#print('='*50 + '\nStart to create rsi signal:')
#data_signal = get_rsi_signal(data_signal)

print('='*50 + '\nFinish signal creation')
write_to_console(data_signal,  '30 second',mode='update')
print('*'*50)


# write_to_mongo(minute_stock_data, '60 second', 'stock', 'minute-stock-data')

# Add signal (TODO)
# agg = agg.withColumn('signal', 
#                      when(col('wclose') > col('wopen'), 1)
#                      .when(col('wclose') < col('wopen'), -1)
#                      .otherwise(0))

print("end")