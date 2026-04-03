import os
import pickle
import logging
from typing import Optional, List, Dict, Any, Tuple

import numpy as np
import pandas as pd
import httpx
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv


# =========================
# LOGGING
# =========================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# =========================
# ENV
# =========================
load_dotenv()

TMDB_API_KEY = os.getenv("TMDB_API_KEY")

TMDB_BASE = "https://api.themoviedb.org/3"
TMDB_IMG_500 = "https://image.tmdb.org/t/p/w500"

if not TMDB_API_KEY:
    logger.warning("⚠️ TMDB_API_KEY not set. TMDB routes may fail.")


# =========================
# PATHS (UPDATED)
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)

DF_PATH = os.getenv("DF_PATH", os.path.join(ROOT_DIR, "model/df.pkl"))
INDICES_PATH = os.getenv("INDICES_PATH", os.path.join(ROOT_DIR, "model/indices.pkl"))
TFIDF_MATRIX_PATH = os.getenv("TFIDF_MATRIX_PATH", os.path.join(ROOT_DIR, "model/tfidf_matrix.pkl"))
TFIDF_PATH = os.getenv("TFIDF_PATH", os.path.join(ROOT_DIR, "model/tfidf.pkl"))
USER_FILE = os.path.join(BASE_DIR, "data", "user_data.json")


# =========================
# FASTAPI APP
# =========================
app = FastAPI(title="Movie Recommender API", version="4.0")
print("TMDB_API_KEY:", TMDB_API_KEY)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================
# GLOBALS
# =========================
df: Optional[pd.DataFrame] = None
indices_obj: Any = None
tfidf_matrix: Any = None
tfidf_obj: Any = None
TITLE_TO_IDX: Optional[Dict[str, int]] = None


# =========================
# MODELS
# =========================
class TMDBMovieCard(BaseModel):
    tmdb_id: int
    title: str
    poster_url: Optional[str] = None
    release_date: Optional[str] = None
    vote_average: Optional[float] = None


class TMDBMovieDetails(BaseModel):
    tmdb_id: int
    title: str
    overview: Optional[str] = None
    release_date: Optional[str] = None
    poster_url: Optional[str] = None
    backdrop_url: Optional[str] = None
    genres: List[dict] = []


class TFIDFRecItem(BaseModel):
    title: str
    score: float
    tmdb: Optional[TMDBMovieCard] = None


class SearchBundleResponse(BaseModel):
    query: str
    movie_details: TMDBMovieDetails
    tfidf_recommendations: List[TFIDFRecItem]
    genre_recommendations: List[TMDBMovieCard]


# =========================
# UTILS
# =========================
def _norm_title(t: str) -> str:
    return str(t).strip().lower()


def make_img_url(path: Optional[str]) -> Optional[str]:
    return f"{TMDB_IMG_500}{path}" if path else None


async def tmdb_get(path: str, params: Dict[str, Any]) -> Dict[str, Any]:
    if not TMDB_API_KEY:
        raise HTTPException(status_code=500, detail="TMDB API key not configured")

    params["api_key"] = TMDB_API_KEY

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.get(f"{TMDB_BASE}{path}", params=params)
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=str(e))

    if r.status_code != 200:
        raise HTTPException(status_code=502, detail=r.text)

    return r.json()


# =========================
# TF-IDF LOGIC
# =========================
def build_title_to_idx_map(indices: Any) -> Dict[str, int]:
    return {_norm_title(k): int(v) for k, v in indices.items()}


def tfidf_recommend_titles(query_title: str, top_n: int = 10):
    idx = TITLE_TO_IDX.get(_norm_title(query_title))
    if idx is None:
        raise HTTPException(status_code=404, detail="Movie not found")

    scores = (tfidf_matrix @ tfidf_matrix[idx].T).toarray().ravel()
    order = np.argsort(-scores)

    results = []
    for i in order:
        if i == idx:
            continue
        title = df.iloc[i]["title"]
        results.append((title, float(scores[i])))
        if len(results) >= top_n:
            break

    return results


# =========================
# STARTUP
# =========================
@app.on_event("startup")
def load_models():
    global df, indices_obj, tfidf_matrix, tfidf_obj, TITLE_TO_IDX

    try:
        with open(DF_PATH, "rb") as f:
            df = pickle.load(f)

        with open(INDICES_PATH, "rb") as f:
            indices_obj = pickle.load(f)

        with open(TFIDF_MATRIX_PATH, "rb") as f:
            tfidf_matrix = pickle.load(f)

        with open(TFIDF_PATH, "rb") as f:
            tfidf_obj = pickle.load(f)

        TITLE_TO_IDX = build_title_to_idx_map(indices_obj)

        logger.info("✅ Models loaded successfully")

    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise RuntimeError(e)


# =========================
# ROUTES
# =========================
# =========================
# ROUTES
# =========================

@app.get("/")
def root():
    return {"message": "Movie Recommender API running"}


@app.get("/health")
def health():
    return {"status": "ok"}


# 🔥 HOME ROUTE (FIXED)
@app.get("/home")
async def home(
    category: str = Query("popular"),
    limit: int = Query(24, ge=1, le=50),
):
    try:
        if category == "trending":
            # fallback to popular (more stable)
            data = await tmdb_get("/movie/popular", {"language": "en-US", "page": 1})
        else:
            data = await tmdb_get(
                f"/movie/{category}",
                {"language": "en-US", "page": 1},
            )

        results = data.get("results", [])

        return [
            {
                "tmdb_id": m["id"],
                "title": m.get("title") or "",
                "poster_url": make_img_url(m.get("poster_path")),
                "release_date": m.get("release_date"),
                "vote_average": m.get("vote_average"),
            }
            for m in results[:limit]
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
user_data = {}
@app.post("/user/watchlist")
def add_watchlist(user_id: str, movie: str):
    if user_id not in user_data:
        user_data[user_id] = {"watchlist": []}
    
    user_data[user_id]["watchlist"].append(movie)
    return {"status": "added"}

@app.post("/user/like")
def like_movie(user_id: str, movie: str):
    user_data.setdefault(user_id, {}).setdefault("liked", []).append(movie)
    return {"status": "liked"}
@app.post("/user/view")
def view_movie(user_id: str, movie: str):
    user_data.setdefault(user_id, {}).setdefault("recent", []).append(movie)
    return {"status": "viewed"}

# 🔥 SEARCH ROUTE (REQUIRED FOR UI)
@app.get("/tmdb/search")
async def tmdb_search(query: str = Query(...)):
    data = await tmdb_get(
        "/search/movie",
        {
            "query": query,
            "language": "en-US",
            "page": 1,
        },
    )
    return data


# 🔥 MOVIE DETAILS
@app.get("/movie/id/{tmdb_id}")
async def movie_details(tmdb_id: int):
    data = await tmdb_get(f"/movie/{tmdb_id}", {"language": "en-US"})

    return {
        "tmdb_id": data["id"],
        "title": data.get("title"),
        "overview": data.get("overview"),
        "release_date": data.get("release_date"),
        "poster_url": make_img_url(data.get("poster_path")),
        "genres": data.get("genres", []),
    }


# 🔥 GENRE RECOMMENDATIONS
@app.get("/recommend/genre")
async def recommend_genre(tmdb_id: int):
    details = await tmdb_get(f"/movie/{tmdb_id}", {"language": "en-US"})

    genres = details.get("genres", [])
    if not genres:
        return []

    genre_id = genres[0]["id"]

    data = await tmdb_get(
        "/discover/movie",
        {
            "with_genres": genre_id,
            "language": "en-US",
            "sort_by": "popularity.desc",
            "page": 1,
        },
    )

    return [
        {
            "tmdb_id": m["id"],
            "title": m.get("title"),
            "poster_url": make_img_url(m.get("poster_path")),
        }
        for m in data.get("results", [])[:12]
        if m["id"] != tmdb_id
    ]


# 🔥 TF-IDF ONLY
@app.get("/recommend/tfidf")
def recommend_tfidf(title: str, top_n: int = 10):
    recs = tfidf_recommend_titles(title, top_n)
    return [{"title": t, "score": s} for t, s in recs]


# 🔥 FULL BUNDLE (USED BY UI)
@app.get("/movie/search")
async def search_bundle(query: str):
    best = await tmdb_get(
        "/search/movie",
        {"query": query, "language": "en-US", "page": 1},
    )

    results = best.get("results", [])
    if not results:
        raise HTTPException(status_code=404, detail="Movie not found")

    movie = results[0]
    tmdb_id = movie["id"]

    details = await tmdb_get(f"/movie/{tmdb_id}", {"language": "en-US"})

    # TF-IDF recs
    tfidf_recs = []
    try:
        recs = tfidf_recommend_titles(details["title"], 6)
        for title, score in recs:
            tmdb_match = await tmdb_get(
                "/search/movie",
                {"query": title, "language": "en-US"},
            )
            tmdb_data = tmdb_match.get("results", [])
            if tmdb_data:
                m = tmdb_data[0]
                tfidf_recs.append(
                    {
                        "title": title,
                        "score": score,
                        "tmdb": {
                            "tmdb_id": m["id"],
                            "title": m["title"],
                            "poster_url": make_img_url(m.get("poster_path")),
                        },
                    }
                )
    except:
        tfidf_recs = []

    # genre recs
    genre_recs = await recommend_genre(tmdb_id)

    return {
        "query": query,
        "movie_details": {
            "tmdb_id": details["id"],
            "title": details.get("title"),
            "overview": details.get("overview"),
            "release_date": details.get("release_date"),
            "poster_url": make_img_url(details.get("poster_path")),
            "genres": details.get("genres", []),
        },
        "tfidf_recommendations": tfidf_recs,
        "genre_recommendations": genre_recs,
    }
