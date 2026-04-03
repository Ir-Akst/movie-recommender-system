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

/* Header */
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

/* Scroll Row */
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
    border-radius: 10px;
}

/* Rating badge */
.rating {
    position: absolute;
    background: #facc15;
    color: black;
    padding: 3px 6px;
    font-size: 12px;
    border-radius: 5px;
    margin: 5px;
}

/* Hide scrollbar */
::-webkit-scrollbar {
    height: 6px;
}
::-webkit-scrollbar-thumb {
    background: #555;
    border-radius: 10px;
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
# HERO SECTION
# =========================
def hero(movie):
    if not movie:
        return

    st.markdown(f"""
    <div style="
        background-image: linear-gradient(to right, rgba(0,0,0,0.9), rgba(0,0,0,0.2)),
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
# HORIZONTAL SCROLL
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

# =========================
# MAIN HOME
# =========================
def show_home():
    with st.sidebar:
        st.write(f"👤 User: {USER_ID[:8]}")

        if st.button("📌 Watchlist"):
            data = api_get("/user/watchlist", {"user_id": USER_ID})
            st.write(data if data else "Empty")

    # Fetch data
    popular = api_get("/home", {"category": "popular", "limit": 15})
    top = api_get("/home", {"category": "top_rated", "limit": 15})
    upcoming = api_get("/home", {"category": "upcoming", "limit": 15})

    if popular:
        hero(popular[0])

    # Sections
    if popular:
        scroll_row("🔥 Popular", popular)

    if top:
        scroll_row("⭐ Top Rated", top)

    if upcoming:
        scroll_row("🎬 Upcoming", upcoming)

# =========================
# RUN
# =========================
show_home()
