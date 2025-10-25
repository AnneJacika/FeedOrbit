import os
import time
import random
from pymongo import MongoClient, UpdateOne
import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, when
from pyspark.ml.recommendation import ALS
from pyspark.ml.feature import StringIndexer
import datetime
import shutil

# ---------------------- Java & Spark environment ----------------------
java_home = r" " #Directory of the java_home
os.environ["JAVA_HOME"] = java_home
os.environ["PATH"] = java_home + r"\bin;" + os.environ["PATH"]
os.environ["PYSPARK_PYTHON"] = r" " # Directory of the python.exe
os.environ["PYSPARK_DRIVER_PYTHON"] = r" " # Directory of the python.exe

print("JAVA_HOME:", os.environ["JAVA_HOME"])
print("java.exe found:", shutil.which("java"))

# ---------------------- MongoDB connection ----------------------
mongo_uri = " " #Mongodb connection URL
client = MongoClient(mongo_uri)
db = client["instaFeed"]

users_col = db["users"]
userEvents_col = db["userEvents"]
recs_col = db["recommendations"]


# ---------------------- Start infinite loop ----------------------
while True:
    try:
        print("📦 Fetching users...")
        users_list = list(users_col.find({}, {"user_id": 1, "tags": 1, "_id": 0}))
        user_ids = [int(u["user_id"]) for u in users_list if "user_id" in u]
        print(f"✅ Loaded {len(user_ids)} users.")

        print("📦 Loading user events...")
        user_events = list(userEvents_col.find({"user_id": {"$in": user_ids}}))
        print(f"✅ Loaded {len(user_events)} user events.")

        if not user_events:
            print("❌ No events found. Waiting for next cycle...")
            time.sleep(60)
            continue

        # ---------------------- Prepare filtered user events ----------------------
        cleaned_user_events = []
        for row in user_events:
            try:
                user_id = int(row.get("user_id", -1))
                post_id = int(row.get("post_id", -1))
            except (ValueError, TypeError):
                continue
            action = str(row.get("action", "view")).strip().lower()
            if post_id != -1:
                cleaned_user_events.append({
                    "user_id": user_id,
                    "post_id": post_id,
                    "action": action
                })

        if not cleaned_user_events:
            print("❌ No valid user events. Waiting for next cycle...")
            time.sleep(60)
            continue

        user_events_df = pd.DataFrame(cleaned_user_events)

        # ---------------------- Start Spark ----------------------
        spark = SparkSession.builder.appName("ALS_UserPost_TagUpdate").getOrCreate()
        userEvents_sdf = spark.createDataFrame(user_events_df)

        # ---------------------- Compute rating ----------------------
        userEvents_sdf = userEvents_sdf.withColumn(
            "rating",
            when(col("action") == "view", 0.1)
            .when(col("action") == "like", 1.0)
            .when(col("action") == "comment", 1.5)
            .when(col("action") == "share", 2.0)
            .otherwise(0.0)
        )

        # ---------------------- Index encoding ----------------------
        user_indexer = StringIndexer(inputCol="user_id", outputCol="user_index").fit(userEvents_sdf)
        post_indexer = StringIndexer(inputCol="post_id", outputCol="post_index").fit(userEvents_sdf)
        als_df = user_indexer.transform(userEvents_sdf)
        als_df = post_indexer.transform(als_df)

        # ---------------------- Train ALS ----------------------
        print("🚀 Training ALS model...")
        als = ALS(
            userCol="user_index",
            itemCol="post_index",
            ratingCol="rating",
            implicitPrefs=True,
            coldStartStrategy="drop",
            maxIter=5,
            rank=10,
            regParam=0.01
        )
        model = als.fit(als_df)

        # ---------------------- Generate recommendations ----------------------
        user_index_to_id = {i: int(label) for i, label in enumerate(user_indexer.labels)}
        post_index_to_id = {i: int(label) for i, label in enumerate(post_indexer.labels)}

        timestamp = datetime.datetime.utcnow().isoformat() + "Z"
        recommendations = []

        print("⚙️ Generating random 9 recommendations for all users based on tags...")
        all_user_recs = model.recommendForAllUsers(50).collect()  # generate more predictions

        for row in all_user_recs:
            user_id = user_index_to_id[int(row["user_index"])]
            user_tags = next((u.get("tags", []) for u in users_list if u["user_id"] == user_id), [])

            recs_list = [
                {
                    "post_id": int(post_index_to_id[int(r["post_index"])]),
                    "score": float(r["rating"])
                }
                for r in row["recommendations"]
            ]

            # ---------------------- Filter posts by matching tags ----------------------
            filtered_recs = []
            for rec in recs_list:
                post = userEvents_col.find_one({"post_id": rec["post_id"]})
                post_tags = post.get("tags", []) if post else []
                if set(user_tags) & set(post_tags):
                    filtered_recs.append(rec)

            if not filtered_recs:
                filtered_recs = recs_list  # fallback if no matching tags

            # ---------------------- Pick random 9 posts ----------------------
            random9 = random.sample(filtered_recs, min(9, len(filtered_recs)))

            recommendations.append({
                "user_id": user_id,
                "tags": user_tags,
                "recommendations": random9,
                "timestamp": timestamp
            })

        # ---------------------- Bulk update MongoDB ----------------------
        bulk_ops = [
            UpdateOne(
                {"user_id": rec["user_id"]},
                {"$set": rec},
                upsert=True
            )
            for rec in recommendations
        ]

        if bulk_ops:
            recs_col.bulk_write(bulk_ops)

        print(f"✅ Updated {len(recommendations)} users with random recommendations at {timestamp}.")
        print("⏱ Waiting 60 seconds before next update...")
        time.sleep(60)

    except Exception as e:
        print("❌ Error occurred:", e)
        print("⏱ Waiting 60 seconds before retrying...")
        time.sleep(60)

