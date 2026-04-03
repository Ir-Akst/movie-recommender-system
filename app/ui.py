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
# CSS (🔥 FIXED + IMPROVED)
# =========================
st.markdown("""
<style>

/* 🌌 Background */
.stApp {
    background: linear-gradient(135deg, #0f172a, #020617);
    color: white;
}

/* Header */
.title {
    text-align: center;
    font-size: 42px;
    font-weight: bold;
}
.subtitle {
    text-align: center;
    color: #94a3b8;
    margin-bottom: 25px;
}

/* Card */
.card {
    background: #0f172a;
    border-radius: 16px;
    padding: 10px;
    transition: 0.3s ease;
    position: relative;
    overflow: hidden;
}

.card:hover {
    transform: translateY(-8px) scale(1.03);
    box-shadow: 0 12px 25px rgba(0,0,0,0.6);
}

/* Poster container */
.poster {
    position: relative;
    border-radius: 12px;
    overflow: hidden;
}

/* Poster image */
.poster img {
    width: 100%;
    border-radius: 12px;
    transition: 0.4s ease;
}

.card:hover .poster img {
    transform: scale(1.08);
}

/* ⭐ FIXED RATING */
.rating {
    position: absolute;
    top: 8px;
    left: 8px;
    background: rgba(250, 204, 21, 0.95);
    color: black;
    font-size: 12px;
    font-weight: bold;
    padding: 4px 6px;
    border-radius: 6px;
    z-index: 10; /* 🔥 FIX */
    backdrop-filter: blur(6px);
}

/* Title */
.movie-title {
    font-size: 14px;
    font-weight: 600;
    margin-top: 8px;
}

/* Buttons */
.stButton>button {
    border-radius: 8px;
    padding: 4px;
    font-size: 12px;
}

/* spacing */
.block-container {
    padding-top: 1rem;
}

</style>
""", unsafe_allow_html=True)

# =========================
# HEADER
# =========================
st.markdown('<div class="title">🎬 AI Movie Recommender</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Discover movies with AI + personalization</div>', unsafe_allow_html=True)

# =========================
# API HELPERS
# =========================
def api_get(path, params=None):
    try:
        r = requests.get(f"{API_BASE}{path}", params=params, timeout=5)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: {e}")
        return None


def api_post(path, movie):
    try:
        requests.post(
            f"{API_BASE}{path}",
            params={"user_id": USER_ID, "movie": movie},
            timeout=5
        )
    except:
        pass

# =========================
# STATE
# =========================
if "selected_movie" not in st.session_state:
    st.session_state.selected_movie = None

# =========================
# POSTER GRID (🔥 FIXED)
# =========================
def poster_grid(movies, cols=5):
    if not movies:
        st.info("No movies found 😕")
        return

    for i in range(0, len(movies), cols):
        row = st.columns(cols)

        for col, m in zip(row, movies[i:i+cols]):
            with col:
                st.markdown('<div class="card">', unsafe_allow_html=True)

                title = m.get("title", "Unknown")
                tmdb_id = m.get("tmdb_id", str(uuid.uuid4()))
                rating = m.get("vote_average")
                poster = m.get("poster_url")

                # 🎬 Poster with rating inside
                st.markdown('<div class="poster">', unsafe_allow_html=True)

                if rating:
                    st.markdown(
                        f'<div class="rating">⭐ {round(rating,1)}</div>',
                        unsafe_allow_html=True
                    )

                if poster:
                    st.image(poster)
                else:
                    st.write("No Image")

                st.markdown('</div>', unsafe_allow_html=True)

                # Title
                st.markdown(f'<div class="movie-title">{title}</div>', unsafe_allow_html=True)

                # Buttons
                c1, c2, c3, c4 = st.columns(4)

                with c1:
                    if st.button("🎬", key=f"view_{tmdb_id}"):
                        api_post("/user/view", title)
                        st.session_state.selected_movie = tmdb_id

                with c2:
                    if st.button("⭐", key=f"watch_{tmdb_id}"):
                        api_post("/user/watchlist", title)

                with c3:
                    if st.button("👍", key=f"like_{tmdb_id}"):
                        api_post("/user/like", title)

                with c4:
                    if st.button("👎", key=f"dislike_{tmdb_id}"):
                        api_post("/user/dislike", title)

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
            if data:
                st.write(data)
            else:
                st.info("Watchlist empty")

    query = st.text_input("🔍 Search movie...")

    if query:
        data = api_get("/tmdb/search", {"query": query})

        if not data or not data.get("results"):
            st.warning("No results found")
            return

        movies = [
            {
                "tmdb_id": m.get("id"),
                "title": m.get("title"),
                "poster_url": f"{TMDB_IMG}{m['poster_path']}" if m.get("poster_path") else None,
                "vote_average": m.get("vote_average")
            }
            for m in data["results"][:15]
        ]

        poster_grid(movies)
        return

    st.markdown(f"## 🎬 {category.title()}")

    movies = api_get("/home", {"category": category, "limit": 15})

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
        return

    col1, col2 = st.columns([1, 2])

    with col1:
        if data.get("poster_url"):
            st.image(data["poster_url"])

    with col2:
        st.title(data.get("title", "No title"))
        st.write(data.get("overview", "No description"))

    st.divider()

    st.subheader("🎯 Recommendations")

    bundle = api_get("/movie/search", {"query": data.get("title")})

    if bundle:
        recs = bundle.get("tfidf_recommendations", [])

        movies = [
            {"tmdb_id": i, "title": r.get("title"), "poster_url": None}
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
