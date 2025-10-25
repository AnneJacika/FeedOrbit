import streamlit as st
from pymongo import MongoClient
import random
import hashlib
import os
from dotenv import load_dotenv
from streamlit_autorefresh import st_autorefresh


load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client['instaFeed']

users_col = db['users']
recommendations_col = db['recommendations']
user_events_col = db['userEvents']


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def assign_random_user_id():
    used_ids = set(users_col.distinct("user_id"))
    available_ids = [i for i in range(1, 1001) if i not in used_ids]
    if not available_ids:
        return None
    return random.choice(available_ids)


post_images = {
    "Sunset at the beach": "images/sunset at the beach.jpg",
    "Morning coffee vibes": "images/morning coffee  vibes.png",
    "City skyline view": "images/city skyline view.jpg",
    "Delicious pasta recipe": "images/delicious pasta receipe.jpg",
    "Hiking adventure": "images/hiking adventure.jpg",
    "Cute puppy photo": "images/cute puppy photo.jpg",
    "Street art discovery": "images/Street Art.jpg",
    "Workout motivation": "images/workout motivation.jpg",
    "Rainy day reading": "images/rainy day reading.jpg",
    "Cozy fireplace moments": "images/cozy fireplace moments.jpg",
    "Fresh fruit smoothie": "images/fresh fruit smoothie.jpg",
    "Mountain sunrise": "images/mountain sunrise.jpg",
    "Yoga session": "images/yoga session.jpg",
    "Garden blooms": "images/garden blooms.jpg",
    "Travel bucket list": "images/Travel Bucket list .jpg",
    "Favorite book quote": "images/favourite book quote.jpg",
    "Weekend getaway": "images/weekend getaway.jpg",
    "Sunset hike": "images/sunset hike.jpg",
    "Beach volleyball fun": "images/beach volleyball fun.jpg",
    "Homemade dessert": "images/homemade dessert.jpg",
    "Vintage car spotting": "images/vintage car spotting.jpeg",
    "Farmers market haul": "images/market haul.jpg",
    "Starry night sky": "images/starry night sky.jpg",
    "Morning meditation": "images/morning meditation.jpg",
    "Street food adventure": "images/street food adventure.jpg",
    "Cute kitten antics": "images/Cute kitten.jpg",
    "Coffee shop vibes": "images/coffee shop vibes.jpg",
    "Scenic bike ride": "images/scenic bike ride.jpg",
    "Aquarium visit": "images/aquarium visit.jpg",
    "Festival lights": "images/festival lights.jpg"
}

post_titles = list(post_images.keys())


st.set_page_config(page_title="FeedOrbit", layout="wide", initial_sidebar_state="auto")

# --- CSS Styling (Lilac + Violet Theme) ---
st.markdown("""
<style>
/* Global font & base */
body, html, [class*="css"] {
    font-family: 'Poppins', sans-serif !important;
    color: #170336 !important;
}

/* Background Gradient */
[data-testid="stAppViewContainer"]  {
    background-color: #cab1f2;  /* solid lilac background */
}

/* Smooth gradient movement */
@keyframes gradientShift {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: #F3E5F5;
    border-right: 2px solid #D1C4E9;
    color: #4A148C;
}

/* Header */
[data-testid="stHeader"] {
    background: rgba(0,0,0,0);
}

h1 {
    font-weight: 900;
    font-size: 3rem;
    text-align: center;
    background: 
        #6a1196;
    border-radius:10px;
    
}



/* Buttons */
.stButton>button {
    background: linear-gradient(90deg, #9C27B0, #7E57C2);
    color: white;
    border-radius: 10px;
    border: 4px solid white; 
    padding: 10px 25px;
    font-weight: 600;
    border: none;
    transition: 0.3s ease;
    box-shadow: 0 3px 10px rgba(124, 77, 255, 0.3);
}
.stButton>button:hover {
    background: linear-gradient(90deg, #7E57C2, #AB47BC);
    transform: scale(1.06);
    box-shadow: 0 6px 15px rgba(124, 77, 255, 0.4);
}

/* Text Inputs */
.stTextInput>div>div>input {
    border-radius: 10px;
    border: 1px solid #B39DDB;
    padding: 10px;
    font-size: 16px;
    background-color: #F3E5F5;        /* soft lilac background */
    color: #4A148C;                   /* dark violet text */
}
.stTextInput>div>div>input::placeholder {
    color: #7E57C2;                   /* slightly darker lilac placeholder */
}

/* Post Card */
.post-card {
    background: rgba(255,255,240,0.95);
    border-radius: 15px;
    padding: 15px;
    margin-bottom: 20px;
    height: auto;
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    transition: all 0.3s ease-in-out;
    box-shadow: 0 4px 10px rgba(155, 89, 182, 0.2);
}
.post-card:hover {
    transform: scale(1.03);
    box-shadow: 0 6px 20px rgba(155, 89, 182, 0.35);
    background: rgba(255,255,255,0.98);
}

/* Info Text */
p, span, label {
    color: #4A148C !important;
}
</style>
""", unsafe_allow_html=True)


st.markdown("<h1 style='text-align:center;'> FeedOrbit </h1>", unsafe_allow_html=True)


if 'page' not in st.session_state:
    st.session_state.page = 'login'
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'username' not in st.session_state:
    st.session_state.username = None

# ----------------------------
# Login / Signup Page
# ----------------------------
if st.session_state.page == 'login':
    st.sidebar.markdown("### Navigation")
    option = st.sidebar.radio("Choose", ("Sign In", "Sign Up"))

    if option == "Sign In":
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            user_doc = users_col.find_one({
                "username": username,
                "password": hash_password(password)
            })
            if not user_doc:
                st.error("Invalid username or password")
            else:
                st.session_state.logged_in = True
                st.session_state.user_id = user_doc['user_id']
                st.session_state.username = username
                st.session_state.page = 'dashboard'
                st.rerun()

    if option == "Sign Up":
        new_username = st.text_input("Choose a username")
        new_password = st.text_input("Choose a password", type="password")

        if st.button("Register"):
            if users_col.find_one({"username": new_username}):
                st.error("Username already exists!")
            else:
                user_id = assign_random_user_id()
                if user_id is None:
                    st.error("All 1–1000 IDs are taken.")
                else:
                    users_col.insert_one({
                        "username": new_username,
                        "password": hash_password(new_password),
                        "user_id": user_id
                    })
                    st.success(f"User registered! Your ID is {user_id}")
                    st.info("Switch to Sign In to log in.")


if st.session_state.page == 'dashboard' and st.session_state.logged_in:
    st.subheader(f" Logged in as: {st.session_state.username}")

    if st.button("Logout"):
        st.session_state.page = 'login'
        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.user_id = None
        st.rerun()

    # Auto-refresh every minute
    st_autorefresh(interval=60_000, limit=None, key="live_refresh")

    
    rec_doc = recommendations_col.find_one(
        {"user_id": st.session_state.user_id},
        sort=[("timestamp", -1)]
    )

    rec_list = []

    if rec_doc and 'recommendations' in rec_doc and len(rec_doc['recommendations']) > 0:
        for rec in rec_doc['recommendations'][:9]:
            post_id = rec['post_id']
            score = rec.get("score", None)

            post_event = user_events_col.find_one({
                "user_id": st.session_state.user_id,
                "post_id": post_id
            })

            if post_event:
                post_name = post_event.get("post_name", f"Post {post_id}")
                tags = post_event.get("tags", [])
            else:
                post_name = post_titles[post_id % len(post_titles)]
                tags = [word.lower() for word in post_name.split() if len(word) > 3]

            rec_list.append({
                "post_id": post_id,
                "post_name": post_name,
                "tags": tags,
                "score": score
            })
    else:
        st.info("No personalized recommendations. Showing default top 9 posts.")
        rec_list = [
            {
                "post_id": i,
                "post_name": post_titles[i % len(post_titles)],
                "tags": [word.lower() for word in post_titles[i % len(post_titles)].split() if len(word) > 3],
                "score": None
            }
            for i in range(9)
        ]

    
    for row in range(3):
        cols = st.columns(3)
        for col_idx in range(3):
            idx = row * 3 + col_idx
            if idx < len(rec_list):
                rec = rec_list[idx]
                post_id = rec.get("post_id")
                post_name = rec.get("post_name")
                img_path = post_images.get(post_name, None)
                score = rec.get("score")
                tags = rec.get("tags", [])
            else:
                post_id = None
                post_name = "Empty"
                img_path = None
                score = None
                tags = []

            with cols[col_idx]:
                st.markdown("<div class='post-card'>", unsafe_allow_html=True)

                if img_path and os.path.exists(img_path):
                    st.image(img_path, use_container_width=True)

                st.markdown(f"<p><b>ID:</b> {post_id} <br><b>{post_name}</b></p>", unsafe_allow_html=True)

                if score is not None:
                    st.markdown(f"<p>Score: {score:.2f}</p>", unsafe_allow_html=True)

                if tags:
                    st.markdown(f"<p>Tags: {', '.join(tags)}</p>", unsafe_allow_html=True)

                st.markdown("</div>", unsafe_allow_html=True)
