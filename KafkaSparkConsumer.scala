import org.apache.spark.sql.SparkSession
import org.apache.spark.sql.functions._
import org.apache.spark.sql.types._

object KafkaSparkConsumer {
  def main(args: Array[String]): Unit = {

    // Create SparkSession with MongoDB connector
    val spark = SparkSession.builder
      .appName("KafkaSparkConsumerWindowed")
      .master("local[*]")
      .config(
        "spark.mongodb.write.connection.uri",
        "mongodb+srv://anishka2310506:K3qDHcjm7vsHpX4X@cluster0.hxrzwvw.mongodb.net/instaFeed?retryWrites=true&w=majority&appName=Cluster0"
      )
      .getOrCreate()

    spark.sparkContext.setLogLevel("WARN")

    // Define schema for user events
    val userEventSchema = new StructType()
      .add("user_id", IntegerType)
      .add("post_id", IntegerType)
      .add("post_name", StringType)
      .add("action", StringType)
      .add("tags", ArrayType(StringType))
      .add("timestamp", StringType)

    // Read stream from Kafka
    val kafkaDF = spark.readStream
      .format("kafka")
      .option("kafka.bootstrap.servers", "localhost:9092")
      .option("subscribe", "user-events")
      .option("startingOffsets", "earliest")
      .option("failOnDataLoss", "false")
      .option("kafka.group.id", "spark-kafka-instafeed-consumer-new")
      .load()

    // Parse JSON and keep Kafka metadata
    val eventsDF = kafkaDF
      .selectExpr(
        "CAST(value AS STRING) as json",
        "partition",
        "offset",
        "timestamp as kafkaTimestamp"
      )
      .select(
        from_json(col("json"), userEventSchema).as("data"),
        col("partition"),
        col("offset"),
        col("kafkaTimestamp")
      )
      .select(
        col("data.*"),
        col("partition").as("debug_partition"),
        col("offset").as("debug_offset"),
        col("kafkaTimestamp").cast("timestamp").as("eventTime")
      )

    // Write raw events to MongoDB and print to console
    val rawToMongo = eventsDF.writeStream
      .outputMode("append")
      .option("checkpointLocation", "checkpoints/rawEvents")
      .foreachBatch { (batchDF: org.apache.spark.sql.Dataset[org.apache.spark.sql.Row], batchId: Long) =>
        println(s"\n==== New Raw Batch Received: Batch ID $batchId ====")
        batchDF.show(truncate = false)

        batchDF.select("debug_partition", "debug_offset", "user_id", "post_id", "action", "eventTime")
          .show(truncate = false)

        batchDF.write
          .format("mongodb")
          .mode("append")
          .option("database", "instaFeed")
          .option("collection", "userEvents")
          .save()
      }
      .start()

    // Windowed aggregation (10 sec window, 5 sec slide) to MongoDB
    val windowedCounts = eventsDF
      .groupBy(
        window(col("eventTime"), "10 seconds", "5 seconds"),
        col("action")
      )
      .count()
      .orderBy("window")

    val windowedToMongo = windowedCounts.writeStream
      .outputMode("complete")
      .option("checkpointLocation", "checkpoints/windowedResults")
      .foreachBatch { (batchDF: org.apache.spark.sql.Dataset[org.apache.spark.sql.Row], batchId: Long) =>
        println(s"\n==== Windowed Aggregation Batch ID $batchId ====")
        batchDF.show(truncate = false)

        batchDF.write
          .format("mongodb")
          .mode("append")
          .option("database", "instaFeed")
          .option("collection", "slidingWindowResults")
          .save()
      }
      .start()

    // Await termination of streams
    spark.streams.awaitAnyTermination()
  }
}
