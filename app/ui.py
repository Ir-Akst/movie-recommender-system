import requests
import streamlit as st
import time
import uuid

# =========================
# CONFIG
# =========================
API_BASE = "https://movie-recommender-system-1-2kes.onrender.com"
TMDB_IMG = "https://image.tmdb.org/t/p/w342"

# =========================
# USER SESSION (MULTI-USER)
# =========================
if "user_id" not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())

USER_ID = st.session_state.user_id

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(page_title="Movie Recommender", page_icon="🎬", layout="wide")

# =========================
# HEADER
# =========================
st.title("🎬 AI Movie Recommender")
st.caption("Personalized recommendations powered by AI")

# =========================
# API HELPERS
# =========================
def api_get(path, params=None):
    try:
        r = requests.get(f"{API_BASE}{path}", params=params, timeout=15)
        if r.status_code == 200:
            return r.json()
    except:
        return None

def api_post(path, movie):
    try:
        requests.post(f"{API_BASE}{path}", params={
            "user_id": USER_ID,
            "movie": movie
        }, timeout=10)
    except:
        pass

# =========================
# SESSION
# =========================
if "selected_movie" not in st.session_state:
    st.session_state.selected_movie = None

# =========================
# POSTER GRID
# =========================
def poster_grid(movies, cols=4):
    if not movies:
        st.warning("No movies found 😢")
        return

    for i in range(0, len(movies), cols):
        row = st.columns(cols)

        for col, m in zip(row, movies[i:i+cols]):
            with col:
                if m.get("poster_url"):
                    st.image(m["poster_url"])

                st.markdown(f"**{m['title']}**")

                # 🎬 View
                if st.button("View", key=f"view_{m['tmdb_id']}"):
                    api_post("/user/view", m["title"])
                    st.session_state.selected_movie = m["tmdb_id"]

                # ⭐ Watchlist
                if st.button("⭐", key=f"watch_{m['tmdb_id']}"):
                    api_post("/user/watchlist", m["title"])
                    st.success("Added")

                # 👍 Like
                if st.button("👍", key=f"like_{m['tmdb_id']}"):
                    api_post("/user/like", m["title"])

                # 👎 Dislike
                if st.button("👎", key=f"dislike_{m['tmdb_id']}"):
                    api_post("/user/dislike", m["title"])

# =========================
# HOME
# =========================
def show_home():
    with st.sidebar:
        st.write(f"👤 User: {USER_ID[:8]}")
        st.divider()

        category = st.selectbox(
            "Category",
            ["popular", "top_rated", "now_playing", "upcoming"]
        )

        if st.button("📌 Watchlist"):
            data = api_get("/user/watchlist", {"user_id": USER_ID})
            st.write(data if data else "Empty")

    # 🔍 Search
    query = st.text_input("Search movie")

    if query:
        data = api_get("/tmdb/search", {"query": query})
        if data:
            movies = [
                {
                    "tmdb_id": m["id"],
                    "title": m["title"],
                    "poster_url": f"{TMDB_IMG}{m['poster_path']}"
                    if m.get("poster_path") else None
                }
                for m in data.get("results", [])[:12]
            ]
            poster_grid(movies)
        return

    # 🎬 Home feed
    st.subheader(category.upper())

    movies = api_get("/home", {"category": category, "limit": 12})

    if movies:
        poster_grid(movies)
    else:
        st.error("Failed to load movies")

# =========================
# DETAILS
# =========================
def show_details(movie_id):
    if st.button("← Back"):
        st.session_state.selected_movie = None
        return

    data = api_get(f"/movie/id/{movie_id}")

    if not data:
        st.error("Error loading")
        return

    col1, col2 = st.columns([1, 2])

    with col1:
        if data.get("poster_url"):
            st.image(data["poster_url"])

    with col2:
        st.title(data["title"])
        st.write(data.get("overview"))

    st.divider()
    st.subheader("Recommendations")

    bundle = api_get("/movie/search", {"query": data["title"]})

    if bundle:
        recs = bundle.get("tfidf_recommendations", [])

        movies = [
            {
                "tmdb_id": i,
                "title": r["title"],
                "poster_url": None
            }
            for i, r in enumerate(recs)
        ]

        poster_grid(movies)

# =========================
# ROUTING
# =========================
if st.session_state.selected_movie:
    show_details(st.session_state.selected_movie)
else:
    show_home()
