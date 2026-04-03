import os
import pickle
import logging
import json
from typing import Optional, List, Dict, Any

import numpy as np
import pandas as pd
import httpx
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
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

# =========================
# PATHS
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)

DF_PATH = os.path.join(ROOT_DIR, "model/df.pkl")
INDICES_PATH = os.path.join(ROOT_DIR, "model/indices.pkl")
TFIDF_MATRIX_PATH = os.path.join(ROOT_DIR, "model/tfidf_matrix.pkl")
TFIDF_PATH = os.path.join(ROOT_DIR, "model/tfidf.pkl")

DATA_FILE = os.path.join(BASE_DIR, "user_data.json")

# =========================
# FASTAPI APP
# =========================
app = FastAPI(title="Movie Recommender API", version="5.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# LOAD / SAVE USER DATA
# =========================
def load_data():
    if not os.path.exists(DATA_FILE):
        return {"watchlist": [], "liked": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

user_data = load_data()

# =========================
# GLOBALS
# =========================
df = None
indices_obj = None
tfidf_matrix = None
tfidf_obj = None
TITLE_TO_IDX = None

# =========================
# UTILS
# =========================
def _norm_title(t: str) -> str:
    return str(t).strip().lower()

def make_img_url(path: Optional[str]) -> Optional[str]:
    return f"{TMDB_IMG_500}{path}" if path else None

async def tmdb_get(path: str, params: Dict[str, Any]) -> Dict[str, Any]:
    if not TMDB_API_KEY:
        raise HTTPException(status_code=500, detail="TMDB API key missing")

    params["api_key"] = TMDB_API_KEY

    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.get(f"{TMDB_BASE}{path}", params=params)

    if r.status_code != 200:
        raise HTTPException(status_code=502, detail=r.text)

    return r.json()

# =========================
# TF-IDF
# =========================
def build_title_to_idx_map(indices):
    return {_norm_title(k): int(v) for k, v in indices.items()}

def tfidf_recommend_titles(query_title: str, top_n=10):
    idx = TITLE_TO_IDX.get(_norm_title(query_title))
    if idx is None:
        raise HTTPException(status_code=404, detail="Movie not found")

    scores = (tfidf_matrix @ tfidf_matrix[idx].T).toarray().ravel()
    order = np.argsort(-scores)

    results = []
    for i in order:
        if i == idx:
            continue
        results.append((df.iloc[i]["title"], float(scores[i])))
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
        df = pickle.load(open(DF_PATH, "rb"))
        indices_obj = pickle.load(open(INDICES_PATH, "rb"))
        tfidf_matrix = pickle.load(open(TFIDF_MATRIX_PATH, "rb"))
        tfidf_obj = pickle.load(open(TFIDF_PATH, "rb"))

        TITLE_TO_IDX = build_title_to_idx_map(indices_obj)

        logger.info("✅ Models loaded")

    except Exception as e:
        logger.error(e)
        raise RuntimeError(e)

# =========================
# ROOT
# =========================
@app.get("/")
def root():
    return {"message": "API running"}

# =========================
# WATCHLIST
# =========================
@app.get("/user/watchlist")
def get_watchlist():
    return user_data["watchlist"]

@app.post("/user/watchlist")
def add_watchlist(movie: str):
    if movie not in user_data["watchlist"]:
        user_data["watchlist"].append(movie)
        save_data(user_data)
    return {"status": "added"}

# =========================
# LIKE
# =========================
@app.get("/user/liked")
def get_liked():
    return user_data["liked"]

@app.post("/user/like")
def like_movie(movie: str):
    if movie not in user_data["liked"]:
        user_data["liked"].append(movie)
        save_data(user_data)
    return {"status": "liked"}

# =========================
# TMDB SEARCH
# =========================
@app.get("/tmdb/search")
async def tmdb_search(query: str):
    return await tmdb_get("/search/movie", {"query": query, "language": "en-US"})

# =========================
# HOME
# =========================
@app.get("/home")
async def home(category: str = "popular", limit: int = 20):
    data = await tmdb_get(f"/movie/{category}", {"language": "en-US", "page": 1})

    return [
        {
            "tmdb_id": m["id"],
            "title": m.get("title"),
            "poster_url": make_img_url(m.get("poster_path")),
        }
        for m in data.get("results", [])[:limit]
    ]

# =========================
# MOVIE DETAILS
# =========================
@app.get("/movie/id/{tmdb_id}")
async def movie_details(tmdb_id: int):
    data = await tmdb_get(f"/movie/{tmdb_id}", {"language": "en-US"})

    return {
        "tmdb_id": data["id"],
        "title": data.get("title"),
        "overview": data.get("overview"),
        "poster_url": make_img_url(data.get("poster_path")),
    }

# =========================
# RECOMMENDATIONS
# =========================
@app.get("/movie/search")
async def search_bundle(query: str):
    search = await tmdb_get("/search/movie", {"query": query})
    results = search.get("results", [])

    if not results:
        raise HTTPException(status_code=404, detail="Movie not found")

    movie = results[0]
    title = movie["title"]

    recs = []
    try:
        tfidf_recs = tfidf_recommend_titles(title, 6)
        recs = [{"title": t, "score": s} for t, s in tfidf_recs]
    except:
        pass

    return {
        "query": query,
        "movie_details": {
            "title": title,
            "overview": movie.get("overview"),
        },
        "tfidf_recommendations": recs,
    }
