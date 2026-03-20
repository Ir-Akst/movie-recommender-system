import requests
import streamlit as st
import os
import time
from dotenv import load_dotenv

# =========================
# ENV
# =========================
load_dotenv()
API_BASE = os.getenv("API_BASE", "http://localhost:8000")
TMDB_IMG = "https://image.tmdb.org/t/p/w342"

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(page_title="Movie Recommender", page_icon="🎬", layout="wide")

# =========================
# CUSTOM CSS
# =========================
st.markdown("""
<style>
body {
    background-color: #0e1117;
}

.main-title {
    text-align: center;
    font-size: 42px;
    font-weight: bold;
    color: #ffffff;
}

.sub-title {
    text-align: center;
    font-size: 18px;
    color: #aaaaaa;
    margin-bottom: 20px;
}

.card {
    background-color: #1c1f26;
    padding: 10px;
    border-radius: 12px;
    text-align: center;
    transition: 0.3s;
}

.card:hover {
    transform: scale(1.03);
}

.stButton>button {
    border-radius: 10px;
    width: 100%;
}
</style>
""", unsafe_allow_html=True)

# =========================
# HEADER
# =========================
st.markdown('<p class="main-title">🎬 AI Movie Recommender</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Discover movies using AI + NLP</p>', unsafe_allow_html=True)

# =========================
# SESSION STATE
# =========================
if "selected_movie" not in st.session_state:
    st.session_state.selected_movie = None


# =========================
# API HELPER
# =========================
@st.cache_data(ttl=600, show_spinner=False)
def api_get_json(path: str, params=None):
    try:
        r = requests.get(f"{API_BASE}{path}", params=params, timeout=20)
        if r.status_code >= 400:
            return None
        return r.json()
    except:
        return None


# =========================
# POSTER GRID
# =========================
def poster_grid(cards, cols=4):
    if not cards:
        st.warning("No movies found 😢")
        return

    for i in range(0, len(cards), cols):
        row = st.columns(cols)

        for col, movie in zip(row, cards[i:i+cols]):
            with col:
                st.markdown('<div class="card">', unsafe_allow_html=True)

                if movie.get("poster_url"):
                    st.image(movie["poster_url"], use_column_width=True)

                st.markdown(f"**{movie['title']}**")

                if st.button("View Details", key=f"{movie['tmdb_id']}"):
                    st.session_state.selected_movie = movie["tmdb_id"]

                st.markdown('</div>', unsafe_allow_html=True)


# =========================
# HOME PAGE
# =========================
def show_home():
    with st.sidebar:
        st.markdown("## 🎯 Explore")
        st.markdown("---")

        category = st.selectbox(
            "Choose Category",
            ["trending", "popular", "top_rated", "now_playing", "upcoming"],
        )

        st.markdown("---")
        st.info("AI-powered recommendations 🔥")

    search_query = st.text_input("🔍 Search for a movie...")

    # SEARCH
    if search_query and len(search_query) > 1:
        time.sleep(0.3)

        with st.spinner("🍿 Searching movies..."):
            data = api_get_json("/tmdb/search", {"query": search_query})

        if data:
            movies = [
                {
                    "tmdb_id": m["id"],
                    "title": m["title"],
                    "poster_url": f"{TMDB_IMG}{m['poster_path']}"
                    if m.get("poster_path")
                    else None,
                }
                for m in data.get("results", [])[:12]
                if m.get("id") and m.get("title")
            ]

            poster_grid(movies)
        else:
            st.error("Search failed.")

        return

    # HOME FEED
    st.subheader(f"🎬 {category.replace('_', ' ').title()}")

    with st.spinner("🍿 Loading movies..."):
        movies = api_get_json("/home", {"category": category, "limit": 12})

    if movies:
        poster_grid(movies)
    else:
        st.error("Failed to load movies.")


# =========================
# DETAILS PAGE
# =========================
def show_details(movie_id):
    if st.button("← Back"):
        st.session_state.selected_movie = None
        return

    with st.spinner("🎬 Loading movie details..."):
        data = api_get_json(f"/movie/id/{movie_id}")

    if not data:
        st.error("Failed to load movie details.")
        return

    col1, col2 = st.columns([1, 2])

    with col1:
        if data.get("poster_url"):
            st.image(data["poster_url"], use_column_width=True)

    with col2:
        st.markdown(f"## 🎬 {data.get('title', '')}")
        st.write("📅 Release:", data.get("release_date", "-"))

        genres = ", ".join([g["name"] for g in data.get("genres", [])])
        st.write("🎭 Genres:", genres if genres else "-")

        st.markdown("### Overview")
        st.write(data.get("overview", "No overview available."))

    st.divider()
    st.subheader("🎯 Recommendations")

    with st.spinner("🤖 Fetching recommendations..."):
        bundle = api_get_json(
            "/movie/search",
            {"query": data.get("title", ""), "tfidf_top_n": 6, "genre_limit": 6},
        )

    if bundle:
        tfidf = bundle.get("tfidf_recommendations", [])
        genre = bundle.get("genre_recommendations", [])

        tfidf_cards = []
        for x in tfidf:
            tmdb = x.get("tmdb", {})
            if tmdb.get("tmdb_id"):
                tfidf_cards.append(
                    {
                        "tmdb_id": tmdb["tmdb_id"],
                        "title": tmdb.get("title"),
                        "poster_url": tmdb.get("poster_url"),
                    }
                )

        if tfidf_cards:
            st.markdown("### 🤖 Similar Movies")
            poster_grid(tfidf_cards)

        if genre:
            st.markdown("### 🎬 More Like This")
            poster_grid(genre)
    else:
        st.info("No recommendations available.")


# =========================
# ROUTING
# =========================
if st.session_state.selected_movie:
    show_details(st.session_state.selected_movie)
else:
    show_home()