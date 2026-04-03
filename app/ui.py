import requests
import streamlit as st
import uuid

# =========================
# CONFIG
# =========================
API_BASE = "https://movie-recommender-system-1-2kes.onrender.com"
TMDB_IMG = "https://image.tmdb.org/t/p/w342"

# =========================
# USER SESSION
# =========================
if "user_id" not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())

USER_ID = st.session_state.user_id

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(page_title="AI Movie Recommender", layout="wide")

# =========================
# 🎨 CUSTOM CSS (MAJOR UPGRADE)
# =========================
st.markdown("""
<style>

body {
    background: linear-gradient(135deg, #020617, #0f172a);
    color: white;
}

/* Title */
h1 {
    color: #38bdf8;
    font-weight: 700;
}

/* Cards */
.movie-card {
    background: rgba(255,255,255,0.05);
    backdrop-filter: blur(12px);
    border-radius: 18px;
    padding: 12px;
    text-align: center;
    transition: 0.3s;
    box-shadow: 0 4px 20px rgba(0,0,0,0.4);
}

.movie-card:hover {
    transform: scale(1.06);
    box-shadow: 0 8px 30px rgba(56,189,248,0.3);
}

/* Poster */
.movie-img {
    border-radius: 12px;
    width: 100%;
}

/* Title */
.movie-title {
    font-size: 15px;
    font-weight: 600;
    margin-top: 8px;
}

/* Buttons */
.stButton button {
    width: 100%;
    border-radius: 10px;
    margin-top: 5px;
    background: linear-gradient(90deg, #38bdf8, #6366f1);
    border: none;
    color: white;
    transition: 0.2s;
}

.stButton button:hover {
    transform: scale(1.05);
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: #020617;
}

/* Search box */
.stTextInput input {
    border-radius: 12px;
    background: #020617;
    color: white;
    border: 1px solid #334155;
}

</style>
""", unsafe_allow_html=True)

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
# 🎬 IMPROVED GRID
# =========================
def poster_grid(movies, cols=5):
    if not movies:
        st.warning("No movies found 😢")
        return

    for i in range(0, len(movies), cols):
        row = st.columns(cols)

        for col, m in zip(row, movies[i:i+cols]):
            with col:

                st.markdown('<div class="movie-card">', unsafe_allow_html=True)

                # Poster
                if m.get("poster_url"):
                    st.markdown(
                        f'<img class="movie-img" src="{m["poster_url"]}">',
                        unsafe_allow_html=True
                    )

                # Title
                st.markdown(
                    f'<div class="movie-title">{m["title"]}</div>',
                    unsafe_allow_html=True
                )

                # Buttons (clean layout)
                c1, c2 = st.columns(2)

                with c1:
                    if st.button("▶ View", key=f"view_{m['tmdb_id']}"):
                        api_post("/user/view", m["title"])
                        st.session_state.selected_movie = m["tmdb_id"]

                with c2:
                    if st.button("⭐ Save", key=f"watch_{m['tmdb_id']}"):
                        api_post("/user/watchlist", m["title"])
                        st.toast("Added to Watchlist ⭐")

                c3, c4 = st.columns(2)

                with c3:
                    if st.button("👍", key=f"like_{m['tmdb_id']}"):
                        api_post("/user/like", m["title"])

                with c4:
                    if st.button("👎", key=f"dislike_{m['tmdb_id']}"):
                        api_post("/user/dislike", m["title"])

                st.markdown('</div>', unsafe_allow_html=True)

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

    query = st.text_input("🔍 Search movie")

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
                for m in data.get("results", [])[:15]
            ]
            poster_grid(movies)
        return

    st.subheader(f"🔥 {category.replace('_', ' ').title()}")

    movies = api_get("/home", {"category": category, "limit": 15})

    if movies:
        poster_grid(movies)
    else:
        st.error("Failed to load movies")

# =========================
# DETAILS PAGE
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
    st.subheader("🎯 Recommended for you")

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
