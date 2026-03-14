# tests/conftest.py
import pytest
import numpy as np
import pandas as pd
from unittest.mock import MagicMock


@pytest.fixture
def sample_embedding_str():
    """
    Embedding เป็น STRING — เหมือนที่เก็บใน PostgreSQL จริง
    matching_engine.py ใช้ ast.literal_eval(movie.embedding)
    ดังนั้น mock ต้องเป็น string ไม่ใช่ list
    """
    vec = [round(float(x), 6) for x in np.random.rand(768).tolist()]
    return str(vec)


@pytest.fixture
def sample_movie_row(sample_embedding_str):
    """
    Mock SQLAlchemy Row ที่ fetchone() คืนมา
    ใช้ MagicMock เพราะ Row ใช้ attribute access (row.title ไม่ใช่ row['title'])
    """
    row = MagicMock()
    row.title = "Blade Runner 2049"
    row.embedding = sample_embedding_str
    row.genre = "Science Fiction"
    return row


@pytest.fixture
def sample_songs_df(sample_embedding_str):
    """
    DataFrame ของ songs — เหมือนที่ pd.read_sql() คืนมา
    embedding column เป็น string เหมือนกัน
    """
    return pd.DataFrame([
        {
            "id": 1, "title": "Dark Fantasy", "artist": "Kanye West",
            "valence": 0.3, "energy": 0.7, "tempo": 140.0,
            "danceability": 0.4, "embedding": sample_embedding_str,
        },
        {
            "id": 2, "title": "Weightless", "artist": "Marconi Union",
            "valence": 0.1, "energy": 0.2, "tempo": 65.0,
            "danceability": 0.2, "embedding": sample_embedding_str,
        },
        {
            "id": 3, "title": "Blinding Lights", "artist": "The Weeknd",
            "valence": 0.7, "energy": 0.8, "tempo": 171.0,
            "danceability": 0.8, "embedding": sample_embedding_str,
        },
    ])


@pytest.fixture
def mock_engine():
    """
    Mock SQLAlchemy engine พร้อม context manager
    matching_engine.py ใช้ pattern: with engine.connect() as conn:
    ต้อง setup __enter__ / __exit__ ไม่งั้น TypeError
    """
    engine = MagicMock()
    mock_conn = MagicMock()
    engine.connect.return_value.__enter__.return_value = mock_conn
    engine.connect.return_value.__exit__.return_value = None
    return engine, mock_conn