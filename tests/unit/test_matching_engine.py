# tests/unit/test_matching_engine.py
import pytest
import pandas as pd
from src.matching_engine import get_alpha, get_movie_audio_profile
from unittest.mock import patch


class TestGetAlpha:

    def test_zero_interactions_returns_high_alpha(self):
        alpha = get_alpha(n_interactions=0)
        assert alpha > 0.8

    def test_many_interactions_returns_low_alpha(self):
        alpha = get_alpha(n_interactions=100)
        assert alpha < 0.2

    def test_midpoint_returns_approximately_half(self):
        alpha = get_alpha(n_interactions=10, midpoint=10)
        assert abs(alpha - 0.5) < 0.001

    def test_alpha_always_between_0_and_1(self):
        for n in [0, 1, 5, 10, 20, 50, 100]:
            alpha = get_alpha(n_interactions=n)
            assert 0.0 < alpha < 1.0

    def test_alpha_is_float(self):
        alpha = get_alpha(n_interactions=5)
        assert isinstance(alpha, float)


class TestGetMovieAudioProfile:

    def test_known_genre_returns_correct_profile(self):
        profile = get_movie_audio_profile("Action")
        assert profile == [0.6, 0.9, 0.7, 0.6]

    def test_unknown_genre_returns_neutral(self):
        profile = get_movie_audio_profile("Mockumentary")
        assert profile == [0.5, 0.5, 0.5, 0.5]

    def test_none_genre_returns_neutral(self):
        profile = get_movie_audio_profile(None)
        assert profile == [0.5, 0.5, 0.5, 0.5]

    def test_comma_separated_uses_primary_only(self):
        assert get_movie_audio_profile("Action, Adventure") == \
               get_movie_audio_profile("Action")

    def test_profile_always_has_4_values(self):
        for genre in ["Action", "Horror", "Comedy", None, "Unknown"]:
            assert len(get_movie_audio_profile(genre)) == 4

    def test_all_values_between_0_and_1(self):
        for genre in ["Action", "Horror", "Comedy", "Drama", "Thriller"]:
            for val in get_movie_audio_profile(genre):
                assert 0.0 <= val <= 1.0

class TestMatchSongs:

    def test_returns_dataframe(self, mock_engine, sample_movie_row, sample_songs_df):
        engine, mock_conn = mock_engine
        mock_conn.execute.return_value.fetchone.return_value = sample_movie_row

        with patch("src.matching_engine.get_engine", return_value=engine):
            with patch("src.matching_engine.pd.read_sql", return_value=sample_songs_df):
                from src.matching_engine import match_songs
                result = match_songs(movie_id=1)

        assert isinstance(result, pd.DataFrame)

    def test_result_has_required_columns(self, mock_engine, sample_movie_row, sample_songs_df):
        engine, mock_conn = mock_engine
        mock_conn.execute.return_value.fetchone.return_value = sample_movie_row

        required_cols = {'id', 'title', 'artist', 'content_score', 'audio_score', 'hybrid_score', 'alpha_used'}

        with patch("src.matching_engine.get_engine", return_value=engine):
            with patch("src.matching_engine.pd.read_sql", return_value=sample_songs_df):
                from src.matching_engine import match_songs
                result = match_songs(movie_id=1)

        assert required_cols.issubset(set(result.columns))

    def test_top_k_limits_results(self, mock_engine, sample_movie_row, sample_songs_df):
        engine, mock_conn = mock_engine
        mock_conn.execute.return_value.fetchone.return_value = sample_movie_row

        with patch("src.matching_engine.get_engine", return_value=engine):
            with patch("src.matching_engine.pd.read_sql", return_value=sample_songs_df):
                from src.matching_engine import match_songs
                result = match_songs(movie_id=1, top_k=2)

        assert len(result) <= 2

    def test_sorted_by_hybrid_score_descending(self, mock_engine, sample_movie_row, sample_songs_df):
        engine, mock_conn = mock_engine
        mock_conn.execute.return_value.fetchone.return_value = sample_movie_row

        with patch("src.matching_engine.get_engine", return_value=engine):
            with patch("src.matching_engine.pd.read_sql", return_value=sample_songs_df):
                from src.matching_engine import match_songs
                result = match_songs(movie_id=1)

        scores = result['hybrid_score'].tolist()
        assert scores == sorted(scores, reverse=True)

    def test_movie_not_found_returns_empty_dataframe(self, mock_engine):
        engine, mock_conn = mock_engine
        mock_conn.execute.return_value.fetchone.return_value = None

        with patch("src.matching_engine.get_engine", return_value=engine):
            from src.matching_engine import match_songs
            result = match_songs(movie_id=99999)

        assert isinstance(result, pd.DataFrame)
        assert result.empty

    def test_no_songs_returns_empty_dataframe(self, mock_engine, sample_movie_row):
        engine, mock_conn = mock_engine
        mock_conn.execute.return_value.fetchone.return_value = sample_movie_row

        empty_df = pd.DataFrame(columns=[
            'id', 'title', 'artist', 'valence',
            'energy', 'tempo', 'danceability', 'embedding'
        ])

        with patch("src.matching_engine.get_engine", return_value=engine):
            with patch("src.matching_engine.pd.read_sql", return_value=empty_df):
                from src.matching_engine import match_songs
                result = match_songs(movie_id=1)

        assert result.empty

class TestSaveMatches:

    @pytest.fixture
    def sample_matches_df(self):
        return pd.DataFrame([
            {
                'id': 1, 'title': 'Dark Fantasy', 'artist': 'Kanye West',
                'content_score': 0.85, 'audio_score': 0.72,
                'hybrid_score': 0.80, 'alpha_used': 0.75
            },
            {
                'id': 2, 'title': 'Weightless', 'artist': 'Marconi Union',
                'content_score': 0.70, 'audio_score': 0.65,
                'hybrid_score': 0.68, 'alpha_used': 0.75
            },
        ])

    def test_execute_called_once_per_song(self, mock_engine, sample_matches_df):
        engine, mock_conn = mock_engine

        with patch("src.matching_engine.get_engine", return_value=engine):
            from src.matching_engine import save_matches
            save_matches(movie_id=1, matches_df=sample_matches_df)

        assert mock_conn.execute.call_count == 2

    def test_commit_called_after_insert(self, mock_engine, sample_matches_df):
        engine, mock_conn = mock_engine

        with patch("src.matching_engine.get_engine", return_value=engine):
            from src.matching_engine import save_matches
            save_matches(movie_id=1, matches_df=sample_matches_df)

        mock_conn.commit.assert_called_once()

    def test_empty_dataframe_no_execute(self, mock_engine):
        engine, mock_conn = mock_engine
        empty_df = pd.DataFrame(columns=[
            'id', 'title', 'artist',
            'content_score', 'audio_score', 'hybrid_score', 'alpha_used'
        ])

        with patch("src.matching_engine.get_engine", return_value=engine):
            from src.matching_engine import save_matches
            save_matches(movie_id=1, matches_df=empty_df)

        assert mock_conn.execute.call_count == 0