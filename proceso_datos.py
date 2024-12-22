from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, avg, window, concat_ws
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, TimestampType
from datetime import datetime

# Crear de Spark session
spark = SparkSession.builder \
    .appName("ConsumoElectricoStreaming") \
    .getOrCreate()

# Esquema de los datos recibidos
schema = StructType([
    StructField("timestamp", StringType(), True),
    StructField("consumo_kwh", DoubleType(), True),
    StructField("id_medidor", StringType(), True),
    StructField("region", StringType(), True),
    StructField("ubicacion", StructType([
        StructField("latitud", DoubleType(), True),
        StructField("longitud", DoubleType(), True)
    ]), True)
])

# Lectura de topics de Kafka 
raw_stream = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "localhost:9092") \
    .option("subscribe", "mediciones_daule,mediciones_samborondon") \
    .load()

# Data -> JSON
parsed_stream = raw_stream.select(from_json(col("value").cast("string"), schema).alias("data")) \
    .selectExpr("data.timestamp", "data.consumo_kwh", "data.region")
parsed_stream = parsed_stream.withColumn("timestamp", col("timestamp").cast(TimestampType()))

# Configuracion de las ventanas de procesamiento + calculo promedios
consumo_promedio = parsed_stream.withWatermark("timestamp", "1 minute") \
    .groupBy(window(col("timestamp"), "1 minute"), col("region")) \
    .agg(avg("consumo_kwh").alias("consumo_promedio"))

# Escritura de datos en HDFS
def write_to_hdfs(df, epoch_id, output_dir):
    current_time = datetime.now().strftime("%Y%m%d%H%M%S") 
    # Validacion de nulos
    if not df.rdd.isEmpty():  
        formatted_df = df.select(
            concat_ws("|",
                      col("region").alias("region"),
                      col("window.start").cast("string").alias("inicio_intervalo"),
                      col("window.end").cast("string").alias("fin_intervalo"),
                      col("consumo_promedio").cast("string").alias("consumo_promedio")
            ).alias("line")
        )
        # Formato del guardo de los resultados en HDFS
        formatted_df.coalesce(1).write \
            .mode("append") \
            .format("text") \
            .option("path", f"{output_dir}/resultados-mediciones-{current_time}") \
            .save()

# Guardado de datos atipicos
consumo_promedio.filter("consumo_promedio > 233") \
    .writeStream \
    .outputMode("update") \
    .trigger(processingTime="1 minute").foreachBatch(lambda df, epoch: write_to_hdfs(df, epoch, "hdfs://localhost:9000/atipicos")) \
    .start()

# Guardado de datos para directorio Daule
consumo_promedio.filter("region = 'Daule'") \
    .writeStream \
    .outputMode("update") \
    .trigger(processingTime="1 minute").foreachBatch(lambda df, epoch: write_to_hdfs(df, epoch, "hdfs://localhost:9000/daule")) \
    .start()

# Guardado de datos para Samborondon
consumo_promedio.filter("region = 'Samborondon'") \
    .writeStream \
    .outputMode("update") \
    .trigger(processingTime="1 minute").foreachBatch(lambda df, epoch: write_to_hdfs(df, epoch, "hdfs://localhost:9000/samborondon")) \
    .start()

spark.streams.awaitAnyTermination()
