# tests/unit/test_generate_embeddings.py
import pytest
import numpy as np
from unittest.mock import patch, MagicMock


# ─────────────────────────────────────────────────────────────────────────────
# PATCH ก่อน import module
#
# ปัญหา: generate_embeddings.py มี model = SentenceTransformer(...) ระดับ top-level
# ทันทีที่ import → โหลด model จริง 400MB
#
# แก้: ใช้ patch เป็น decorator บน class ทั้งหมด
# patch("sentence_transformers.SentenceTransformer") ก่อน module load
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_model():
    """Mock SentenceTransformer model ที่ return numpy array ขนาดถูกต้อง"""
    model = MagicMock()
    # encode() คืน 2D array: shape (n_texts, 768)
    model.encode.return_value = np.random.rand(3, 768).astype(np.float32)
    return model


@pytest.fixture
def mock_engine():
    """Mock SQLAlchemy engine พร้อม context manager"""
    engine = MagicMock()
    mock_conn = MagicMock()
    engine.connect.return_value.__enter__.return_value = mock_conn
    engine.connect.return_value.__exit__.return_value = None
    return engine, mock_conn


# ─── Test make_movie_text() ───────────────────────────────────────────────────

@patch("sentence_transformers.SentenceTransformer")
class TestMakeMovieText:
    """
    ทดสอบ make_movie_text() — pure function ไม่ต้อง mock อะไรเพิ่ม
    แค่ต้อง patch SentenceTransformer ไว้ก่อนเพื่อกัน model load
    """

    def test_contains_title(self, mock_st):
        from src.generate_embeddings import make_movie_text
        row = {"title": "Blade Runner 2049", "genre": "Sci-Fi", "overview": "A story"}
        result = make_movie_text(row)
        assert "Blade Runner 2049" in result

    def test_contains_genre(self, mock_st):
        from src.generate_embeddings import make_movie_text
        row = {"title": "Test", "genre": "Action", "overview": "Overview"}
        result = make_movie_text(row)
        assert "Action" in result

    def test_contains_overview(self, mock_st):
        from src.generate_embeddings import make_movie_text
        row = {"title": "Test", "genre": "Drama", "overview": "A deep story"}
        result = make_movie_text(row)
        assert "A deep story" in result

    def test_returns_string(self, mock_st):
        from src.generate_embeddings import make_movie_text
        row = {"title": "T", "genre": "G", "overview": "O"}
        assert isinstance(make_movie_text(row), str)


# ─── Test make_song_text() ────────────────────────────────────────────────────

@patch("sentence_transformers.SentenceTransformer")
class TestMakeSongText:

    def test_contains_title_and_artist(self, mock_st):
        from src.generate_embeddings import make_song_text
        row = {
            "title": "Dark Fantasy", "artist": "Kanye West",
            "valence": 0.3, "energy": 0.7,
            "tempo": 140.0, "danceability": 0.4
        }
        result = make_song_text(row)
        assert "Dark Fantasy" in result
        assert "Kanye West" in result

    def test_contains_audio_features(self, mock_st):
        from src.generate_embeddings import make_song_text
        row = {
            "title": "Test", "artist": "Artist",
            "valence": 0.5, "energy": 0.8,
            "tempo": 120.0, "danceability": 0.6
        }
        result = make_song_text(row)
        assert "0.5" in result   # valence
        assert "0.8" in result   # energy

    def test_returns_string(self, mock_st):
        from src.generate_embeddings import make_song_text
        row = {
            "title": "T", "artist": "A",
            "valence": 0.1, "energy": 0.1,
            "tempo": 100.0, "danceability": 0.1
        }
        assert isinstance(make_song_text(row), str)


# ─── Test embed_movies() ──────────────────────────────────────────────────────

@patch("sentence_transformers.SentenceTransformer")
class TestEmbedMovies:

    def _make_mock_rows(self):
        """สร้าง mock rows เหมือนที่ mappings().fetchall() คืนมา"""
        return [
            {"id": 1, "title": "Blade Runner 2049", "genre": "Sci-Fi", "overview": "Story A"},
            {"id": 2, "title": "Interstellar", "genre": "Drama", "overview": "Story B"},
            {"id": 3, "title": "Her", "genre": "Romance", "overview": "Story C"},
        ]

    def test_encode_called_once(self, mock_st, mock_model, mock_engine):
        """model.encode() ต้องถูกเรียก 1 ครั้ง (batch encode ทีเดียว)"""
        engine, mock_conn = mock_engine
        mock_rows = self._make_mock_rows()
        mock_conn.execute.return_value.mappings.return_value.fetchall.return_value = mock_rows

        # inject mock_model เข้าไปแทน global model
        with patch("src.generate_embeddings.model", mock_model):
            from src.generate_embeddings import embed_movies
            embed_movies(engine)

        mock_model.encode.assert_called_once()

    def test_update_called_for_each_row(self, mock_st, mock_model, mock_engine):
        """
        UPDATE ต้องถูกเรียก 1 ครั้งต่อ movie
        3 movies → execute ถูกเรียก 1 (SELECT) + 3 (UPDATE) = 4 ครั้ง
        """
        engine, mock_conn = mock_engine
        mock_rows = self._make_mock_rows()
        mock_conn.execute.return_value.mappings.return_value.fetchall.return_value = mock_rows
        mock_model.encode.return_value = np.random.rand(3, 768).astype(np.float32)

        with patch("src.generate_embeddings.model", mock_model):
            from src.generate_embeddings import embed_movies
            embed_movies(engine)

        # SELECT 1 ครั้ง + UPDATE 3 ครั้ง = 4 ครั้ง
        assert mock_conn.execute.call_count == 4

    def test_commit_called(self, mock_st, mock_model, mock_engine):
        """ต้อง commit หลัง UPDATE ทุกตัว"""
        engine, mock_conn = mock_engine
        mock_rows = self._make_mock_rows()
        mock_conn.execute.return_value.mappings.return_value.fetchall.return_value = mock_rows
        mock_model.encode.return_value = np.random.rand(3, 768).astype(np.float32)

        with patch("src.generate_embeddings.model", mock_model):
            from src.generate_embeddings import embed_movies
            embed_movies(engine)

        mock_conn.commit.assert_called_once()

    def test_embedding_stored_as_string(self, mock_st, mock_model, mock_engine):
        """
        embedding ต้องถูก convert เป็น string ก่อน UPDATE
        เพราะ PostgreSQL เก็บเป็น text แล้วค่อย parse ด้วย ast.literal_eval ตอนดึง
        """
        engine, mock_conn = mock_engine
        mock_rows = [{"id": 1, "title": "T", "genre": "G", "overview": "O"}]
        mock_conn.execute.return_value.mappings.return_value.fetchall.return_value = mock_rows
        mock_model.encode.return_value = np.random.rand(1, 768).astype(np.float32)

        with patch("src.generate_embeddings.model", mock_model):
            from src.generate_embeddings import embed_movies
            embed_movies(engine)

        # ดึง params ที่ส่งไปใน UPDATE call ล่าสุด
        last_call_args = mock_conn.execute.call_args_list[-1]
        params = last_call_args[0][1]  # positional arg ที่ 2 คือ dict params
        assert isinstance(params["emb"], str), \
            f"embedding ต้องเป็น string ก่อน UPDATE, got {type(params['emb'])}"
        
@patch("sentence_transformers.SentenceTransformer")
class TestEmbedSongs:

    def _make_mock_rows(self):
        return [
            {"id": 1, "title": "Dark Fantasy", "artist": "Kanye West",
             "valence": 0.3, "energy": 0.7, "tempo": 140.0, "danceability": 0.4},
            {"id": 2, "title": "Weightless", "artist": "Marconi Union",
             "valence": 0.1, "energy": 0.2, "tempo": 65.0, "danceability": 0.2},
            {"id": 3, "title": "Blinding Lights", "artist": "The Weeknd",
             "valence": 0.7, "energy": 0.8, "tempo": 171.0, "danceability": 0.8},
        ]

    def test_encode_called_once(self, mock_st, mock_model, mock_engine):
        engine, mock_conn = mock_engine
        mock_rows = self._make_mock_rows()
        mock_conn.execute.return_value.mappings.return_value.fetchall.return_value = mock_rows

        with patch("src.generate_embeddings.model", mock_model):
            from src.generate_embeddings import embed_songs
            embed_songs(engine)

        mock_model.encode.assert_called_once()

    def test_update_called_for_each_row(self, mock_st, mock_model, mock_engine):
        engine, mock_conn = mock_engine
        mock_rows = self._make_mock_rows()
        mock_conn.execute.return_value.mappings.return_value.fetchall.return_value = mock_rows
        mock_model.encode.return_value = np.random.rand(3, 768).astype(np.float32)

        with patch("src.generate_embeddings.model", mock_model):
            from src.generate_embeddings import embed_songs
            embed_songs(engine)

        # SELECT 1 ครั้ง + UPDATE 3 ครั้ง = 4
        assert mock_conn.execute.call_count == 4

    def test_commit_called(self, mock_st, mock_model, mock_engine):
        engine, mock_conn = mock_engine
        mock_rows = self._make_mock_rows()
        mock_conn.execute.return_value.mappings.return_value.fetchall.return_value = mock_rows
        mock_model.encode.return_value = np.random.rand(3, 768).astype(np.float32)

        with patch("src.generate_embeddings.model", mock_model):
            from src.generate_embeddings import embed_songs
            embed_songs(engine)

        mock_conn.commit.assert_called_once()