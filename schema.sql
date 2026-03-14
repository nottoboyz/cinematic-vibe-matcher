-- ============================================
-- CINEMATIC VIBE MATCHER — DATABASE SCHEMA
-- ============================================

-- Load pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================
-- TABLE 1: movies
-- ============================================
CREATE TABLE movies (
    id          SERIAL PRIMARY KEY,
    tmdb_id     INTEGER NOT NULL UNIQUE,
    title       TEXT NOT NULL,
    overview    TEXT,
    embedding   VECTOR(768),
    vote_avg    NUMERIC(3,1) CHECK (vote_avg >= 0 AND vote_avg <= 10),
    created_at  TIMESTAMP DEFAULT NOW()
);

-- ============================================
-- TABLE 2: songs
-- ============================================
CREATE TABLE songs (
    id          SERIAL PRIMARY KEY,
    title       TEXT NOT NULL,
    artist      TEXT NOT NULL,
    valence     NUMERIC(4,3) CHECK (valence >= 0 AND valence <= 1),
    energy      NUMERIC(4,3) CHECK (energy >= 0 AND energy <= 1),
    tempo       NUMERIC(6,2),
    embedding   VECTOR(768),
    created_at  TIMESTAMP DEFAULT NOW(),
    UNIQUE(title, artist)
);

-- ============================================
-- TABLE 3: vibe_matches
-- ============================================
CREATE TABLE vibe_matches (
    id          SERIAL PRIMARY KEY,
    movie_id    INTEGER NOT NULL REFERENCES movies(id) ON DELETE CASCADE,
    song_id     INTEGER NOT NULL REFERENCES songs(id) ON DELETE CASCADE,
    score       NUMERIC(5,4) CHECK (score >= 0 AND score <= 1),
    algorithm   TEXT DEFAULT 'cosine_similarity',
    matched_at  TIMESTAMP DEFAULT NOW(),
    UNIQUE(movie_id, song_id)
);

-- ============================================
-- REGULAR INDEXES
-- ============================================
CREATE INDEX idx_movies_tmdb_id ON movies(tmdb_id);
CREATE INDEX idx_vibe_matches_movie ON vibe_matches(movie_id);
CREATE INDEX idx_vibe_matches_song ON vibe_matches(song_id);

-- ============================================
-- VECTOR INDEXES (IVFFlat)
-- ============================================
CREATE INDEX idx_movies_embedding ON movies
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

CREATE INDEX idx_songs_embedding ON songs
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- ============================================
-- SAMPLE DATA (สำหรับฝึก Query)
-- ============================================
INSERT INTO movies (tmdb_id, title, overview, vote_avg) VALUES
    (550,   'Fight Club',        'An insomniac office worker forms an underground fight club.',    8.4),
    (13,    'Forrest Gump',      'The presidencies of Kennedy through Clinton unfold through one man.', 8.5),
    (238,   'The Godfather',     'The aging patriarch of an organized crime dynasty.',             9.2),
    (680,   'Pulp Fiction',      'The lives of two mob hitmen intertwine in Los Angeles.',         8.9),
    (19404, 'Dilwale Dulhania',  'A young man falls in love during a trip across Europe.',         8.1);

INSERT INTO songs (title, artist, valence, energy, tempo) VALUES
    ('Bohemian Rhapsody',   'Queen',            0.369, 0.401, 71.00),
    ('Blinding Lights',     'The Weeknd',       0.614, 0.730, 171.01),
    ('Lose Yourself',       'Eminem',           0.349, 0.920, 86.01),
    ('Creep',               'Radiohead',        0.098, 0.497, 92.01),
    ('Happy',               'Pharrell Williams',0.962, 0.788, 160.02),
    ('Hurt',                'Johnny Cash',      0.048, 0.336, 67.00),
    ('Eye of the Tiger',    'Survivor',         0.498, 0.944, 109.02);

INSERT INTO vibe_matches (movie_id, song_id, score, algorithm) VALUES
    (1, 3, 0.9120, 'cosine_similarity'),   -- Fight Club + Lose Yourself
    (1, 4, 0.8830, 'cosine_similarity'),   -- Fight Club + Creep
    (2, 5, 0.9450, 'cosine_similarity'),   -- Forrest Gump + Happy
    (3, 6, 0.9010, 'cosine_similarity'),   -- Godfather + Hurt
    (4, 1, 0.8750, 'cosine_similarity'),   -- Pulp Fiction + Bohemian Rhapsody
    (4, 3, 0.8600, 'cosine_similarity');   -- Pulp Fiction + Lose Yourself
