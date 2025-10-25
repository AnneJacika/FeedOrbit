name := "KafkaSyntheticProducer"
version := "0.1"
scalaVersion := "2.12.18"

libraryDependencies ++= Seq(
  "org.apache.kafka" %% "kafka" % "3.5.0",
  "org.apache.kafka" % "kafka-clients" % "3.5.0",
  "com.typesafe.play" %% "play-json" % "2.10.0",  // For JSON formatting
  "org.apache.spark" %% "spark-sql" % "3.5.6",
  "org.apache.spark" %% "spark-sql-kafka-0-10" % "3.5.6",
  "org.mongodb.spark" %% "mongo-spark-connector" % "10.4.1"
  
  
)
