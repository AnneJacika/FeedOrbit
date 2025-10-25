import java.util.Properties
import org.apache.kafka.clients.producer.{KafkaProducer, ProducerRecord}
import scala.util.Random
import play.api.libs.json._

object SyntheticUserEvents extends App {

  val props = new Properties()
  props.put("bootstrap.servers", "localhost:9092")
  props.put("key.serializer", "org.apache.kafka.common.serialization.StringSerializer")
  props.put("value.serializer", "org.apache.kafka.common.serialization.StringSerializer")

  val producer = new KafkaProducer[String, String](props)
  sys.addShutdownHook { producer.close() }

  val topic = "user-events"
  val actions = Seq("like", "comment", "share", "view")
  val rnd = new Random()

  val postNames = Seq(
    "Sunset at the beach", "Morning coffee vibes", "City skyline view", "Delicious pasta recipe",
    "Hiking adventure", "Cute puppy photo", "Street art discovery", "Workout motivation",
    "Rainy day reading", "Cozy fireplace moments", "Fresh fruit smoothie", "Mountain sunrise",
    "Yoga session", "Garden blooms", "Travel bucket list", "Favorite book quote",
    "Weekend getaway", "Sunset hike", "Beach volleyball fun", "Homemade dessert",
    "Vintage car spotting", "Farmers market haul", "Starry night sky", "Morning meditation",
    "Street food adventure", "Cute kitten antics", "Coffee shop vibes", "Scenic bike ride",
    "Aquarium visit", "Festival lights"
  )

  val postTagsMap: Map[String, Seq[String]] = Map(
    "Sunset at the beach" -> Seq("travel", "nature", "photography"),
    "Morning coffee vibes" -> Seq("lifestyle", "food", "photography"),
    "City skyline view" -> Seq("travel", "photography", "architecture"),
    "Delicious pasta recipe" -> Seq("food", "cooking", "lifestyle"),
    "Hiking adventure" -> Seq("travel", "fitness", "nature"),
    "Cute puppy photo" -> Seq("pets", "cute", "photography"),
    "Street art discovery" -> Seq("art", "photography", "urban"),
    "Workout motivation" -> Seq("fitness", "lifestyle", "health"),
    "Rainy day reading" -> Seq("lifestyle", "books", "cozy"),
    "Cozy fireplace moments" -> Seq("lifestyle", "home", "cozy"),
    "Fresh fruit smoothie" -> Seq("food", "health", "lifestyle"),
    "Mountain sunrise" -> Seq("nature", "travel", "photography"),
    "Yoga session" -> Seq("fitness", "health", "lifestyle"),
    "Garden blooms" -> Seq("nature", "photography", "hobby"),
    "Travel bucket list" -> Seq("travel", "lifestyle", "adventure"),
    "Favorite book quote" -> Seq("books", "lifestyle", "inspiration"),
    "Weekend getaway" -> Seq("travel", "lifestyle", "photography"),
    "Sunset hike" -> Seq("travel", "nature", "fitness"),
    "Beach volleyball fun" -> Seq("sports", "fitness", "travel"),
    "Homemade dessert" -> Seq("food", "cooking", "lifestyle"),
    "Vintage car spotting" -> Seq("hobby", "photography", "lifestyle"),
    "Farmers market haul" -> Seq("food", "lifestyle", "photography"),
    "Starry night sky" -> Seq("nature", "photography", "travel"),
    "Morning meditation" -> Seq("lifestyle", "health", "mindfulness"),
    "Street food adventure" -> Seq("food", "travel", "lifestyle"),
    "Cute kitten antics" -> Seq("pets", "cute", "photography"),
    "Coffee shop vibes" -> Seq("lifestyle", "food", "photography"),
    "Scenic bike ride" -> Seq("fitness", "travel", "nature"),
    "Aquarium visit" -> Seq("travel", "photography", "education"),
    "Festival lights" -> Seq("lifestyle", "travel", "photography")
  )

  case class UserEvent(user_id: Int, post_id: Int, post_name: String, action: String, tags: Seq[String], timestamp: String)
  implicit val userEventWrites: Writes[UserEvent] = Json.writes[UserEvent]

  println("Starting synthetic data generation... Press Ctrl+C to stop.")

  while (true) {
    val postIndex = rnd.nextInt(postNames.length) // 0..29
    val postName = postNames(postIndex)
    val eventTags = postTagsMap.getOrElse(postName, Seq("general"))

    val startId = postIndex * 20 + 1  // 1, 21, 41, ...
    val endId = startId + 19          // 20, 40, 60, ...
    val postId = rnd.nextInt(endId - startId + 1) + startId

    val event = UserEvent(
      user_id = rnd.nextInt(1000) + 1,
      post_id = postId,
      post_name = postName,
      action = actions(rnd.nextInt(actions.length)),
      tags = eventTags,
      timestamp = java.time.Instant.now.toString
    )

    producer.send(new ProducerRecord[String, String](topic, Json.stringify(Json.toJson(event))))
    println(s"Produced: ${Json.stringify(Json.toJson(event))}")

    Thread.sleep(500)
  }
}
