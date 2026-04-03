import streamlit as st
import requests
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

if "selected_movie" not in st.session_state:
    st.session_state.selected_movie = None

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(page_title="AI Movie Recommender", layout="wide")

# =========================
# MODERN UI CSS
# =========================
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #020617, #0f172a);
    color: white;
}

.title {
    text-align: center;
    font-size: 42px;
    font-weight: bold;
}
.subtitle {
    text-align: center;
    color: #94a3b8;
    margin-bottom: 20px;
}

/* Scroll row */
.scroll-row {
    display: flex;
    overflow-x: auto;
    gap: 15px;
    padding-bottom: 10px;
}
.scroll-item {
    min-width: 180px;
    transition: 0.3s;
}
.scroll-item:hover {
    transform: scale(1.08);
}

/* Poster */
.poster {
    width: 100%;
    border-radius: 10px;
}

/* Buttons */
.stButton>button {
    border-radius: 8px;
    padding: 4px;
    font-size: 12px;
}
</style>
""", unsafe_allow_html=True)

# =========================
# HEADER
# =========================
st.markdown('<div class="title">🎬 AI Movie Recommender</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Netflix-style UI with AI recommendations</div>', unsafe_allow_html=True)

# =========================
# API FUNCTIONS
# =========================
def api_get(path, params=None):
    try:
        r = requests.get(f"{API_BASE}{path}", params=params)
        if r.status_code == 200:
            return r.json()
    except:
        return None

def api_post(path, movie):
    try:
        requests.post(f"{API_BASE}{path}", params={
            "user_id": USER_ID,
            "movie": movie
        })
    except:
        pass

# =========================
# HERO
# =========================
def hero(movie):
    if not movie:
        return

    st.markdown(f"""
    <div style="
        background-image: linear-gradient(to right, rgba(0,0,0,0.9), rgba(0,0,0,0.3)),
        url('{movie.get("poster_url","")}');
        background-size: cover;
        border-radius: 16px;
        padding: 40px;
        margin-bottom: 20px;
    ">
        <h1 style="color:white;">{movie["title"]}</h1>
        <p style="color:#ccc;">🔥 Featured Movie</p>
    </div>
    """, unsafe_allow_html=True)

# =========================
# SCROLL ROW
# =========================
def scroll_row(title, movies):
    st.markdown(f"## {title}")

    html = '<div class="scroll-row">'
    for m in movies:
        html += f"""
        <div class="scroll-item">
            <img src="{m.get("poster_url","")}" class="poster"/>
            <p style="font-size:13px;">{m["title"]}</p>
        </div>
        """
    html += "</div>"

    st.markdown(html, unsafe_allow_html=True)

    # Buttons (below row)
    for m in movies[:10]:
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button(f"🎬 {m['title'][:8]}", key=f"view_{m['tmdb_id']}"):
                api_post("/user/view", m["title"])
                st.session_state.selected_movie = m["tmdb_id"]

        with col2:
            if st.button("⭐", key=f"watch_{m['tmdb_id']}"):
                api_post("/user/watchlist", m["title"])

        with col3:
            if st.button("👍", key=f"like_{m['tmdb_id']}"):
                api_post("/user/like", m["title"])

        with col4:
            if st.button("👎", key=f"dislike_{m['tmdb_id']}"):
                api_post("/user/dislike", m["title"])

# =========================
# HOME PAGE
# =========================
def show_home():
    with st.sidebar:
        st.write(f"👤 User: {USER_ID[:8]}")

        if st.button("📌 Watchlist"):
            data = api_get("/user/watchlist", {"user_id": USER_ID})
            st.write(data if data else "Empty")

    query = st.text_input("🔍 Search movie...")

    if query:
        data = api_get("/tmdb/search", {"query": query})
        if data:
            movies = [
                {
                    "tmdb_id": m["id"],
                    "title": m["title"],
                    "poster_url": f"{TMDB_IMG}{m['poster_path']}"
                    if m.get("poster_path") else None,
                }
                for m in data.get("results", [])[:12]
            ]
            scroll_row("🔍 Results", movies)
        return

    # Fetch sections
    popular = api_get("/home", {"category": "popular", "limit": 15})
    top = api_get("/home", {"category": "top_rated", "limit": 15})
    upcoming = api_get("/home", {"category": "upcoming", "limit": 15})

    if popular:
        hero(popular[0])

    if popular:
        scroll_row("🔥 Popular", popular)

    if top:
        scroll_row("⭐ Top Rated", top)

    if upcoming:
        scroll_row("🎬 Upcoming", upcoming)

# =========================
# DETAILS PAGE
# =========================
def show_details(movie_id):
    if st.button("← Back"):
        st.session_state.selected_movie = None
        return

    data = api_get(f"/movie/id/{movie_id}")

    if not data:
        st.error("Failed to load")
        return

    col1, col2 = st.columns([1,2])

    with col1:
        if data.get("poster_url"):
            st.image(data["poster_url"])

    with col2:
        st.title(data["title"])
        st.write(data.get("overview"))

    st.divider()
    st.subheader("🎯 Recommendations")

    bundle = api_get("/movie/search", {"query": data["title"]})

    if bundle:
        recs = bundle.get("tfidf_recommendations", [])

        movies = [
            {"tmdb_id": i, "title": r["title"], "poster_url": None}
            for i, r in enumerate(recs)
        ]

        scroll_row("Recommended", movies)

# =========================
# ROUTING
# =========================
if st.session_state.selected_movie:
    show_details(st.session_state.selected_movie)
else:
    show_home()
