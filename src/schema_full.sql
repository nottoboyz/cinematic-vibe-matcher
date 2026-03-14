CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE movies (
    id           SERIAL PRIMARY KEY,
    tmdb_id      INTEGER NOT NULL UNIQUE,
    title        TEXT NOT NULL,
    overview     TEXT,
    genre        TEXT,
    release_date TEXT,
    popularity   NUMERIC(10,3),
    vote_avg     NUMERIC(3,1),
    embedding    VECTOR(768),
    created_at   TIMESTAMP DEFAULT NOW()
);

CREATE TABLE songs (
    id          SERIAL PRIMARY KEY,
    spotify_id  TEXT,
    title       TEXT NOT NULL,
    artist      TEXT NOT NULL,
    valence     NUMERIC(4,3),
    energy      NUMERIC(4,3),
    tempo       NUMERIC(6,2),
    danceability NUMERIC(4,3),
    embedding   VECTOR(768),
    created_at  TIMESTAMP DEFAULT NOW(),
    UNIQUE(title, artist)
);

CREATE TABLE vibe_matches (
    id             SERIAL PRIMARY KEY,
    movie_id       INTEGER NOT NULL REFERENCES movies(id) ON DELETE CASCADE,
    song_id        INTEGER NOT NULL REFERENCES songs(id) ON DELETE CASCADE,
    score          NUMERIC(5,4),
    hybrid_score   NUMERIC(5,4),
    n_interactions INTEGER DEFAULT 0,
    algorithm      TEXT DEFAULT 'cosine_similarity',
    matched_at     TIMESTAMP DEFAULT NOW(),
    UNIQUE(movie_id, song_id)
);

CREATE TABLE user_feedback (
    id         SERIAL PRIMARY KEY,
    movie_id   INTEGER NOT NULL REFERENCES movies(id) ON DELETE CASCADE,
    song_id    INTEGER NOT NULL REFERENCES songs(id) ON DELETE CASCADE,
    rating     NUMERIC(3,1) CHECK (rating >= 1 AND rating <= 5),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(movie_id, song_id)
);