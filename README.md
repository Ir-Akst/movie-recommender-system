# 🎬 AI Movie Recommender System

A modern **AI-powered Movie Recommendation Web App** built with:

* 🎨 **Streamlit (Frontend)**
* ⚡ **FastAPI (Backend)**
* 🤖 **Machine Learning (TF-IDF / Content-Based Filtering)**

This project demonstrates **end-to-end system design**: UI → API → ML → Personalization.

---

## 🚀 Live Features

### 🔍 Movie Discovery

* Search movies using real-time API
* Browse categories:

  * Popular
  * Top Rated
  * Now Playing
  * Upcoming

---

### 🎯 Personalization

* 👍 Like / 👎 Dislike movies
* ⭐ Add to Watchlist
* 👀 Track viewing history
* Session-based user tracking using UUID

---

### 🤖 AI Recommendation Engine

* Content-based filtering using **TF-IDF**
* Cosine similarity for recommendations
* Suggests movies similar to selected title

---

### 🎨 UI Highlights

* 🌌 Dark gradient modern UI
* 🎞️ Interactive movie cards
* ⭐ Floating rating badge (fixed overlay bug)
* ✨ Hover animations (zoom + elevation)
* 📱 Responsive grid layout

---

## 🏗️ Project Structure

```
movie-recommender/
│
├── app/
│   ├── ui.py              # 🎬 Streamlit frontend
│   └── main.py            # ⚡ FastAPI backend
│
├── model/
│   └── recommender.py     # ML logic (TF-IDF)
│
├── data/
│   └── movies.csv         # dataset
│
├── requirements.txt
├── .gitignore
└── README.md
```

---

## ⚙️ Installation & Setup

### 1️⃣ Clone Repository

```bash
git clone https://github.com/your-username/movie-recommender.git
cd movie-recommender
```

---

### 2️⃣ Create Virtual Environment

```bash
python -m venv venv

# Activate
venv\Scripts\activate      # Windows
source venv/bin/activate   # Mac/Linux
```

---

### 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

---

### 4️⃣ Run Backend (FastAPI)

```bash
uvicorn app.main:app --reload
```

---

### 5️⃣ Run Frontend (Streamlit)

```bash
streamlit run app/ui.py
```

---

## 🌐 API Endpoints

| Method | Endpoint     | Description         |
| ------ | ------------ | ------------------- |
| GET    | `/movies`    | Get movie list      |
| GET    | `/search`    | Search movies       |
| POST   | `/like`      | Like a movie        |
| GET    | `/recommend` | Get recommendations |

---

## 🧠 How Recommendation Works

### Current Approach:

* TF-IDF vectorization on movie metadata
* Cosine similarity to compute similarity
* Returns top similar movies

---

### Example Flow:

```
User selects movie → Convert to vector → Compare with dataset → Return similar movies
```

---

## 🔮 Future Improvements


* Sentence Transformers (Embeddings)
* FAISS / Vector Database
* Hybrid recommendation (content + collaborative)

---


## 🛠️ Tech Stack

| Layer    | Technology   |
| -------- | ------------ |
| Frontend | Streamlit    |
| Backend  | FastAPI      |
| ML       | Scikit-learn |
| Data     | Pandas       |
| API      | TMDB         |

---

## ⚠️ Known Issues

* Missing posters for some movies
* Cold-start problem (new users)
* Basic recommendation logic (can be improved)

---

## 🤝 Contributing

```bash
git checkout -b feature-name
git commit -m "Add feature"
git push origin feature-name
```

---

## 👨‍💻 Author

**Akshat**
AI/ML Enthusiast | Data Science | FinTech Explorer

---

## ⭐ Support

If you like this project:

* ⭐ Star the repo
* 🍴 Fork it
* 📢 Share it

---
