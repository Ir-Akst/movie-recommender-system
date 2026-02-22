import requests
import streamlit as st

API_BASE = "https://movie-recommender-system-bacq.onrender.com"
TMDB_IMG = "https://image.tmdb.org/t/p/w342"

st.set_page_config(page_title="Movie Recommender", page_icon="🎬", layout="wide")

if "selected_movie" not in st.session_state:
    st.session_state.selected_movie = None

@st.cache_data(ttl=600)
def api_get_json(path: str, params: dict | None = None):
    try:
        r = requests.get(f"{API_BASE}{path}", params=params, timeout=20)
        if r.status_code >= 400:
            return None
        return r.json()
    except:
        return None

def poster_grid(cards, cols=4):
    if not cards:
        st.info("No movies to show.")
        return
    for i in range(0, len(cards), cols):
        row = st.columns(cols)
        for col, movie in zip(row, cards[i:i+cols]):
            with col:
                if movie.get("poster_url"):
                    st.image(movie["poster_url"], use_column_width=True)
                if st.button(movie["title"], key=f"{movie['tmdb_id']}"):
                    st.session_state.selected_movie = movie["tmdb_id"]

def show_home():
    st.title("🎬 Movie Recommender")
    with st.sidebar:
        category = st.selectbox(
            "Home Category",
            ["trending", "popular", "top_rated", "now_playing", "upcoming"],
        )

    search_query = st.text_input("Search Movie")

    if search_query and len(search_query) > 1:
        data = api_get_json("/tmdb/search", {"query": search_query})
        if data:
            if isinstance(data, dict) and "results" in data:
                movies = [
                    {
                        "tmdb_id": m["id"],
                        "title": m["title"],
                        "poster_url": f"{TMDB_IMG}{m['poster_path']}"
                        if m.get("poster_path")
                        else None,
                    }
                    for m in data["results"][:12]
                    if m.get("id") and m.get("title")
                ]
            else:
                movies = data[:12]
            poster_grid(movies)
        else:
            st.warning("Search failed.")
        return

    st.subheader(f"{category.replace('_', ' ').title()}")
    movies = api_get_json("/home", {"category": category, "limit": 12})
    if movies:
        poster_grid(movies)
    else:
        st.warning("Failed to load home feed.")

def show_details(movie_id):
    if st.button("← Back"):
        st.session_state.selected_movie = None
        return

    data = api_get_json(f"/movie/id/{movie_id}")
    if not data:
        st.error("Failed to load movie details.")
        return

    col1, col2 = st.columns([1, 2])
    with col1:
        if data.get("poster_url"):
            st.image(data["poster_url"], use_column_width=True)
    with col2:
        st.title(data.get("title", ""))
        st.write("Release:", data.get("release_date", "-"))
        genres = ", ".join([g["name"] for g in data.get("genres", [])])
        st.write("Genres:", genres if genres else "-")
        st.markdown("### Overview")
        st.write(data.get("overview", "No overview available."))

    st.divider()
    st.subheader("Recommendations")

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
            st.markdown("Similar Movies")
            poster_grid(tfidf_cards)

        if genre:
            st.markdown("More Like This")
            poster_grid(genre)
    else:
        st.info("No recommendations available.")

if st.session_state.selected_movie:
    show_details(st.session_state.selected_movie)
else:
    show_home()
