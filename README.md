<div align="center">

# ?? Cinematic Vibe Matcher

**An NLP-powered system that analyzes the emotional DNA of movies and matches them with songs that share the same vibe — using semantic embeddings and hybrid similarity search.**

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-pgvector-336791?style=for-the-badge&logo=postgresql&logoColor=white)](https://github.com/pgvector/pgvector)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io)

</div>

---

## ?? What Is This?

Most recommendation systems match movies and songs by genre tags or metadata.
**Cinematic Vibe Matcher goes deeper** — it reads a movie's plot, tone, and emotional weight,
converts that meaning into a 768-dimensional semantic vector, and finds songs that truly *feel* the same.

> *Think: "Interstellar" paired with Hans Zimmer's "Time" — not because they're both sci-fi/orchestral,
> but because both carry the same emotional signature of vast loneliness and quiet hope.*

---

## ? Features

| Feature | Description |
|---|---|
| ?? **Semantic NLP** | Movie overviews embedded with `all-mpnet-base-v2` (768-dim) via sentence-transformers |
| ?? **Hybrid Matching** | Combines semantic cosine similarity + audio feature profiles (valence, energy, tempo) |
| ? **Adaptive Alpha** | Sigmoid-based weight tuning — balances content vs audio score per movie automatically |
| ??? **pgvector Search** | Fast vector similarity queries in PostgreSQL — no external vector DB needed |
| ?? **Interactive Dashboard** | Dark cinematic Streamlit UI with live Plotly score distributions |
| ?? **Feedback Loop** | Users can rate matches; feedback stored for future model improvement |
| ?? **One-Command Deploy** | Full stack runs with a single `docker compose up` |

---

## ??? Architecture
```
ฺฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฟ
ณ                    CINEMATIC VIBE MATCHER                   ณ
ภฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤู

  ฺฤฤฤฤฤฤฤฤฤฤฤฤฤฤฟ    ฺฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฟ
  ณ  Data Layer  ณ    ณ           NLP Pipeline               ณ
  ณ              ณ    ณ                                      ณ
  ณ  TMDB API ฤฤณ    ณ  Movie Overview                      ณ
  ณ  IMDb Data   ณ    ณ      ณ                               ณ
  ณ  MusicBrainz ณ    ณ                                     ณ
  ภฤฤฤฤฤฤ?ฤฤฤฤฤฤฤู    ณ  sentence-transformers               ณ
         ณ            ณ  (all-mpnet-base-v2, 768-dim)        ณ
                     ณ      ณ                               ณ
  ฺฤฤฤฤฤฤฤฤฤฤฤฤฤฤฟ    ณ                                     ณ
  ณ  PostgreSQL  ณฤฤฤณ  Embedding Vector ฤฤ pgvector       ณ
  ณ  + pgvector  ณ    ณ                                      ณ
  ณ              ณ    ณ  spaCy (NER) + VADER (Sentiment)     ณ
  ณ  movies      ณ    ภฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤู
  ณ  songs       ณ
  ณ  vibe_matchesณ    ฺฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฟ
  ณ  feedback    ณ    ณ        Hybrid Matching Engine        ณ
  ภฤฤฤฤฤฤ?ฤฤฤฤฤฤฤู    ณ                                      ณ
         ณ            ณ  cosine_sim(movie_emb, song_emb)     ณ
                     ณ         x  alpha  (content)          ณ
  ฺฤฤฤฤฤฤฤฤฤฤฤฤฤฤฟ    ณ  +                                   ณ
  ณ  FastAPI     ณ    ณ  audio_profile_match(genre, song)    ณ
  ณ              ณ    ณ         x (1-alpha) (audio)          ณ
  ณ  GET /recommend   ณ                                      ณ
  ณ  POST /feedback   ณ  alpha = sigmoid(popularity, vote)   ณ
  ภฤฤฤฤฤฤ?ฤฤฤฤฤฤฤู    ภฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤฤู
         ณ
         
  ฺฤฤฤฤฤฤฤฤฤฤฤฤฤฤฟ
  ณ  Streamlit   ณ
  ณ  Dashboard   ณ
  ณ              ณ
  ณ  Dark Cinema ณ
  ณ  UI + Plotly ณ
  ภฤฤฤฤฤฤฤฤฤฤฤฤฤฤู
```

---

## ?? Quick Start

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running

### Run the full stack
```bash
git clone https://github.com/nottoboyz/cinematic-vibe-matcher.git
cd cinematic-vibe-matcher

# Copy environment file
cp .env.example .env
# Edit .env with your values if needed

# Launch everything
docker compose up
```

| Service | URL |
|---|---|
| ?? Dashboard | http://localhost:8501 |
| ? API | http://localhost:8000 |
| ?? API Docs | http://localhost:8000/docs |
| ??? Database | localhost:5432 |

---

## ??? Tech Stack

### Core ML / NLP
| Tool | Role |
|---|---|
| `sentence-transformers` | Semantic text embeddings (768-dim) |
| `spaCy` (en_core_web_sm) | Named Entity Recognition |
| `VADER` | Sentiment analysis |
| `scikit-learn` | Cosine similarity, preprocessing |

### Backend & Data
| Tool | Role |
|---|---|
| `FastAPI` + `async SQLAlchemy` | REST API with async DB queries |
| `PostgreSQL` + `pgvector` | Vector storage & similarity search |
| `Pydantic` | Request/response validation |

### Frontend & Infra
| Tool | Role |
|---|---|
| `Streamlit` | Interactive dashboard |
| `Plotly` | Score distribution charts |
| `Docker Compose` | Full-stack orchestration |

---

## ?? Project Structure
```
cinematic-vibe-matcher/
?ฤฤ src/
ณ   ?ฤฤ dashboard/
ณ   ณ   ภฤฤ app.py              # Streamlit dark cinematic UI
ณ   ?ฤฤ api/
ณ   ณ   ภฤฤ main.py             # FastAPI endpoints
ณ   ?ฤฤ nlp/
ณ   ณ   ภฤฤ processor.py        # NLPProcessor class
ณ   ?ฤฤ matching/
ณ   ณ   ภฤฤ engine.py           # Hybrid matching engine
ณ   ภฤฤ data_pipeline/
ณ       ?ฤฤ fetch_movies.py     # TMDB data ingestion
ณ       ภฤฤ fetch_songs.py      # Song data ingestion
?ฤฤ docker-compose.yml
?ฤฤ Dockerfile.api
?ฤฤ Dockerfile.dashboard
?ฤฤ requirements.txt
?ฤฤ .env.example
ภฤฤ README.md
```

---

## ?? API Reference

### `GET /recommend/{movie_id}`
Returns top-10 song matches for a given movie.
```json
{
  "movie_id": 1,
  "title": "Interstellar",
  "matches": [
    {
      "song_id": 42,
      "title": "Time",
      "artist": "Hans Zimmer",
      "hybrid_score": 0.847,
      "content_score": 0.891,
      "audio_score": 0.762
    }
  ]
}
```

### `POST /feedback`
Submit a rating for a movie-song match.
```json
{
  "movie_id": 1,
  "song_id": 42,
  "rating": 5
}
```

---

## ?? How the Matching Works
```
hybrid_score = (? ? content_score) + ((1 - ?) ? audio_score)

where:
  content_score = cosine_similarity(movie_embedding, song_embedding)
  audio_score   = genre_audio_profile_match(movie_genre, song_features)
  ?             = sigmoid(movie_popularity, vote_average)
                   high popularity/rating  trust content more
                   low signal movies       rely more on audio features
```

This adaptive alpha means the system **self-tunes** based on how much data exists about each movie — a key design decision that mirrors production ML systems.

---

## ?? Dataset

| Table | Count | Source |
|---|---|---|
| Movies | 40 | TMDB API |
| Songs | 39 | MusicBrainz + Mock Audio Features* |
| Vibe Matches | 390 | Generated (40 ? 10 top matches) |

*\*Note: Audio features use genre-based mock profiles due to Spotify API policy changes in 2024. Real audio analysis can be plugged in via [Essentia](https://essentia.upf.edu/).*

---

## ??? Roadmap

- [ ] Real audio feature extraction with Essentia
- [ ] User playlist import (Spotify OAuth)
- [ ] Feedback-driven model retraining loop
- [ ] Deployment to Railway / Render

---

## ?? Author

**Wongsatorn Paikoh (Notto)**
Digitech Student at Suranaree University of Technology — building real-world systems that bridge data science and business impact.


[![GitHub](https://img.shields.io/badge/GitHub-nottoboyz-181717?style=flat&logo=github)](https://github.com/nottoboyz)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Wongsatorn-0A66C2?style=flat&logo=linkedin)](https://www.linkedin.com/in/wongsatorn-paikoh-bb46953a9/)

---

<div align="center">
  <sub>Built with ? and a genuine love for both cinema and music.</sub>
</div>
