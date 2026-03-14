import streamlit as st
import time
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

@st.cache_resource
def get_engine():
    url = (
        f"postgresql://"
        f"{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
        f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}"
        f"/{os.getenv('DB_NAME')}"
    )
    return create_engine(url)

st.set_page_config(
    page_title="Cinematic Vibe Matcher",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── DEMO DATA ────────────────────────────────────────────────────────────────
DEMO_VIBES = [
    {"film": "Blade Runner 2049", "genre": "Sci-Fi · Drama",    "song": "Blade Runner Blues", "score": 0.89,
     "bars": [("valence",12,"#e05878"),("energy",31,"#3ecfcf"),("tempo",68,"#9b72e8")]},
    {"film": "The Dark Knight",   "genre": "Action · Thriller", "song": "Ominous Voice",      "score": 0.86,
     "bars": [("valence",25,"#e05878"),("energy",85,"#3ecfcf"),("tempo",95,"#9b72e8")]},
    {"film": "La La Land",        "genre": "Romance · Musical", "song": "City of Stars",      "score": 0.92,
     "bars": [("valence",82,"#e05878"),("energy",54,"#3ecfcf"),("tempo",75,"#9b72e8")]},
    {"film": "Dune: Part Two",    "genre": "Sci-Fi · Epic",     "song": "Ripples in the Sand","score": 0.88,
     "bars": [("valence",18,"#e05878"),("energy",72,"#3ecfcf"),("tempo",88,"#9b72e8")]},
]

# ── CSS ──────────────────────────────────────────────────────────────────────
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;0,700;1,400;1,600&family=Outfit:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

html, body, [class*="css"] { font-family: 'Outfit', sans-serif !important; }

.stApp { background: #07080f !important; color: #eeeef5 !important; }
.main .block-container { background: transparent !important; padding-top: 0 !important; max-width: 1200px !important; }

section[data-testid="stSidebar"] { background: #0c0d18 !important; border-right: 1px solid rgba(255,255,255,0.07) !important; }
section[data-testid="stSidebar"] * { color: #eeeef5 !important; }

section[data-testid="stSidebar"] .stSelectbox > div > div {
  background: #11121f !important; border: 1px solid rgba(255,255,255,0.12) !important; border-radius: 3px !important;
}
section[data-testid="stSidebar"] .stButton > button {
  width: 100% !important; background: transparent !important;
  border: 1px solid #d4a843 !important; color: #f0c060 !important;
  font-family: 'JetBrains Mono', monospace !important; font-size: 11px !important;
  letter-spacing: 2px !important; text-transform: uppercase !important;
  padding: 12px !important; border-radius: 3px !important;
}
section[data-testid="stSidebar"] .stButton > button:hover {
  background: rgba(212,168,67,0.1) !important;
}

.stSelectbox > div > div { background: #11121f !important; border: 1px solid rgba(255,255,255,0.12) !important; border-radius: 3px !important; }
.stTextInput input, .stTextArea textarea { background: #11121f !important; border: 1px solid rgba(255,255,255,0.12) !important; color: #eeeef5 !important; border-radius: 3px !important; }

::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: #07080f; }
::-webkit-scrollbar-thumb { background: #40405a; border-radius: 2px; }

#MainMenu, footer, header { visibility: hidden !important; }

@keyframes pulse { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:0.4;transform:scale(0.7)} }
@keyframes fadein { from{opacity:0;transform:translateY(8px)} to{opacity:1;transform:translateY(0)} }
@keyframes scanline { 0%{opacity:0;top:0} 30%{opacity:1} 100%{opacity:0;top:100%} }
</style>
"""

# ── API HELPERS ──────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def fetch_movies():
    try:
        engine = get_engine()
        with engine.connect() as conn:
            rows = conn.execute(text("""
                SELECT id,
                       title,
                       genre,
                       SUBSTRING(release_date, 1, 4)::int AS year,
                       overview,
                       vote_avg
                FROM   movies
                ORDER  BY popularity DESC
            """)).fetchall()
        movies = [dict(r._mapping) for r in rows]
        return movies, False

    except Exception as e:
        st.error(f"DB Error: {e}")
        return [], True            

def fetch_recommendations(movie_id, top_k):
    try:
        engine = get_engine()
        with engine.connect() as conn:
            rows = conn.execute(
                text("""
                    SELECT vm.song_id,
                           s.title        AS song_title,
                           s.artist,
                           s.valence,
                           s.energy,
                           s.tempo,
                           s.danceability,
                           vm.content_score,
                           vm.audio_score,
                           vm.hybrid_score
                    FROM   vibe_matches vm
                    JOIN   songs s ON s.id = vm.song_id
                    WHERE  vm.movie_id = :movie_id
                    ORDER  BY vm.hybrid_score DESC
                    LIMIT  :top_k
                """),
                {"movie_id": movie_id, "top_k": top_k}
            ).fetchall()

        matches = [dict(r._mapping) for r in rows]
        for m in matches:
            m["similarity_score"] = m["hybrid_score"]
        return matches, False

    except Exception as e:
        st.error(f"DB Error: {e}")
        return [], True

def post_feedback(movie_id, song_id, rating, note):
    try:
        engine = get_engine()
        with engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO feedback (movie_id, song_id, rating)
                VALUES (:movie_id, :song_id, :rating)
            """), {"movie_id": movie_id, "song_id": song_id, "rating": rating})
        return True
    except Exception as e:
        st.error(f"DB Error: {e}")
        return False

# ── HTML BUILDERS ────────────────────────────────────────────────────────────
def build_bars(bars):
    html = ""
    for label, val, color in bars:
        html += (
            '<div style="display:flex;align-items:center;gap:10px;margin-bottom:8px">'
            '<div style="font-size:10px;color:#7070a0;font-family:JetBrains Mono,monospace;width:72px;flex-shrink:0">' + label + '</div>'
            '<div style="flex:1;height:5px;background:rgba(255,255,255,0.06);border-radius:3px;overflow:hidden">'
            '<div style="width:' + str(val) + '%;height:100%;background:' + color + ';border-radius:3px"></div>'
            '</div>'
            '<div style="font-size:10px;color:#7070a0;font-family:JetBrains Mono,monospace;width:28px;text-align:right">' + str(val) + '</div>'
            '</div>'
        )
    return html

def build_badges():
    data = [
        ("Python · SQL",    "rgba(212,168,67,0.35)", "rgba(212,168,67,0.1)",  "#f0c060"),
        ("NLP · Embeddings","rgba(62,207,207,0.3)",  "rgba(62,207,207,0.1)",  "#3ecfcf"),
        ("pgvector · ML",   "rgba(155,114,232,0.3)", "rgba(155,114,232,0.1)", "#9b72e8"),
        ("TMDB · Spotify",  "rgba(224,88,120,0.3)",  "rgba(224,88,120,0.1)",  "#e05878"),
        ("FastAPI · Docker","rgba(62,207,142,0.3)",  "rgba(62,207,142,0.1)",  "#3ecf8e"),
    ]
    html = ""
    for text, bc, bg, fc in data:
        html += (
            '<span style="padding:5px 14px;font-size:10px;font-family:JetBrains Mono,monospace;'
            'border-radius:3px;border:1px solid ' + bc + ';background:' + bg + ';color:' + fc + ';font-weight:500;margin-right:6px">'
            + text + '</span>'
        )
    return html

# ── HERO ─────────────────────────────────────────────────────────────────────
def render_hero(vibe):
    bars_html  = build_bars(vibe["bars"])
    badges_html = build_badges()

    html = (
        '<div style="position:relative;padding:3.5rem 2.5rem 2.5rem;'
        'background:radial-gradient(ellipse 80% 60% at 65% 0%,rgba(212,168,67,0.08),transparent 70%),'
        'radial-gradient(ellipse 50% 40% at 5% 85%,rgba(155,114,232,0.07),transparent 60%),#07080f;'
        'border-bottom:1px solid rgba(255,255,255,0.07);overflow:hidden;margin:-1rem -1rem 2rem -1rem">'

        # Scan line
        '<div style="position:absolute;top:0;left:0;right:0;height:1px;'
        'background:linear-gradient(90deg,transparent,#d4a843,transparent);'
        'animation:scanline 6s ease-in-out infinite;opacity:0.6"></div>'

        '<div style="display:grid;grid-template-columns:1fr 320px;gap:3rem;align-items:center;position:relative;z-index:1">'

        # LEFT
        '<div style="animation:fadein 0.6s ease forwards">'
        '<div style="display:flex;align-items:center;gap:10px;margin-bottom:1.2rem">'
        '<div style="width:6px;height:6px;background:#d4a843;border-radius:50%;animation:pulse 2s infinite"></div>'
        '<span style="font-family:JetBrains Mono,monospace;font-size:10px;letter-spacing:3px;text-transform:uppercase;color:#d4a843">'
        'Portfolio Project — Data Engineering + ML</span>'
        '</div>'
        '<div style="font-family:Cormorant Garamond,serif;font-size:clamp(2.6rem,4.5vw,4.2rem);'
        'font-weight:700;line-height:1.0;margin-bottom:1rem;color:#fff;text-shadow:0 0 80px rgba(212,168,67,0.2)">'
        'Cinematic<br><span style="color:#f0c060;font-style:italic">Vibe</span><br>Matcher'
        '</div>'
        '<div style="font-size:14px;color:#7070a0;line-height:1.8;max-width:520px;margin-bottom:1.6rem;font-weight:300">'
        'ระบบวิเคราะห์ความหมายแฝงของภาพยนตร์ด้วย NLP Semantic Embeddings<br>'
        'เพื่อจับคู่กับเพลงที่มี "ความรู้สึก" เดียวกัน ผ่าน pgvector Similarity Search'
        '</div>'
        '<div style="display:flex;flex-wrap:wrap;gap:8px">' + badges_html + '</div>'
        '</div>'

        # RIGHT — vibe box
        '<div style="background:#11121f;border:1px solid rgba(255,255,255,0.12);padding:1.4rem;'
        'position:relative;overflow:hidden;animation:fadein 0.8s ease 0.2s both">'
        '<div style="position:absolute;inset:0;pointer-events:none;'
        'background:radial-gradient(circle at 80% 20%,rgba(212,168,67,0.07),transparent 60%)"></div>'
        '<div style="font-family:JetBrains Mono,monospace;font-size:9px;letter-spacing:2.5px;'
        'text-transform:uppercase;color:#7070a0;margin-bottom:1rem">◈ Live Vibe Match Demo</div>'
        '<div style="font-family:Cormorant Garamond,serif;font-size:1.2rem;font-weight:600;color:#fff;margin-bottom:4px">'
        + vibe["film"] + '</div>'
        '<div style="font-size:10px;color:#7070a0;font-family:JetBrains Mono,monospace;margin-bottom:1rem;letter-spacing:1px">'
        + vibe["genre"] + '</div>'
        '<div style="margin-bottom:1.2rem">' + bars_html + '</div>'
        '<div style="font-size:9px;letter-spacing:2px;text-transform:uppercase;color:#7070a0;'
        'font-family:JetBrains Mono,monospace;margin-bottom:6px">Top Matched Song</div>'
        '<div style="padding:8px 12px;background:#161728;border:1px solid rgba(255,255,255,0.07);'
        'display:flex;justify-content:space-between;align-items:center">'
        '<span style="font-size:13px;font-weight:500;color:#eeeef5">' + vibe["song"] + '</span>'
        '<span style="font-family:JetBrains Mono,monospace;font-size:13px;color:#f0c060;font-weight:600">'
        + str(vibe["score"]) + '</span>'
        '</div>'
        '</div>'

        '</div></div>'
    )
    st.markdown(html, unsafe_allow_html=True)

# ── SECTION HEADER ───────────────────────────────────────────────────────────
def section_header(num, title, subtitle="", accent="#d4a843"):
    sub = '<div style="font-size:13px;color:#7070a0;font-weight:300;line-height:1.7">' + subtitle + '</div>' if subtitle else ""
    html = (
        '<div style="margin-bottom:1.8rem">'
        '<div style="font-family:JetBrains Mono,monospace;font-size:9px;letter-spacing:3px;text-transform:uppercase;color:#7070a0;margin-bottom:4px">' + num + '</div>'
        '<div style="font-family:Cormorant Garamond,serif;font-size:1.9rem;font-weight:700;color:#fff;margin-bottom:6px">' + title + '</div>'
        + sub +
        '<div style="height:1px;background:linear-gradient(90deg,' + accent + ',transparent);margin-top:1rem;opacity:0.5"></div>'
        '</div>'
    )
    st.markdown(html, unsafe_allow_html=True)

# ── SIDEBAR ──────────────────────────────────────────────────────────────────
def render_sidebar(movies, offline):
    with st.sidebar:
        st.markdown(
            '<div style="padding:1.5rem 0 1.2rem;border-bottom:1px solid rgba(255,255,255,0.07);margin-bottom:1.5rem">'
            '<div style="font-family:JetBrains Mono,monospace;font-size:9px;letter-spacing:3px;text-transform:uppercase;color:#7070a0;margin-bottom:8px">Control Panel</div>'
            '<div style="font-family:Cormorant Garamond,serif;font-size:1.4rem;font-weight:700;color:#fff">'
            'Find Your <span style="color:#f0c060;font-style:italic">Vibe</span></div>'
            '</div>',
            unsafe_allow_html=True
        )

        if offline:
            st.markdown(
                '<div style="padding:8px 10px;background:rgba(212,168,67,0.08);border:1px solid rgba(212,168,67,0.25);'
                'border-radius:3px;margin-bottom:1rem;font-family:JetBrains Mono,monospace;font-size:10px;color:#d4a843">'
                '⚠ Demo Mode — API offline</div>',
                unsafe_allow_html=True
            )

        st.markdown('<div style="font-family:JetBrains Mono,monospace;font-size:10px;letter-spacing:2px;text-transform:uppercase;color:#7070a0;margin-bottom:6px">Select Film</div>', unsafe_allow_html=True)
        options = {m["title"] + " (" + str(m.get("year","")) + ")": m["id"] for m in movies}
        selected = st.selectbox("film", list(options.keys()), label_visibility="collapsed")
        movie_id = options[selected]

        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
        st.markdown('<div style="font-family:JetBrains Mono,monospace;font-size:10px;letter-spacing:2px;text-transform:uppercase;color:#7070a0;margin-bottom:6px">Top K Results</div>', unsafe_allow_html=True)
        top_k = st.slider("topk", 1, 20, 5, label_visibility="collapsed")

        st.markdown("<div style='height:1.2rem'></div>", unsafe_allow_html=True)
        search = st.button("⟶  Find Vibes", use_container_width=True)

        st.markdown(
            '<div style="margin-top:2rem;padding:1rem;background:#07080f;border:1px solid rgba(255,255,255,0.07)">'
            '<div style="font-family:JetBrains Mono,monospace;font-size:9px;letter-spacing:2px;text-transform:uppercase;color:#7070a0;margin-bottom:10px">Session Info</div>'
            '<div style="display:flex;justify-content:space-between;margin-bottom:5px">'
            '<span style="font-size:11px;color:#7070a0;font-family:JetBrains Mono,monospace">Films</span>'
            '<span style="font-size:11px;color:#f0c060;font-family:JetBrains Mono,monospace">' + str(len(movies)) + '</span>'
            '</div>'
            '<div style="display:flex;justify-content:space-between">'
            '<span style="font-size:11px;color:#7070a0;font-family:JetBrains Mono,monospace">Top K</span>'
            '<span style="font-size:11px;color:#3ecfcf;font-family:JetBrains Mono,monospace">' + str(top_k) + '</span>'
            '</div>'
            '</div>'
            '<div style="margin-top:1.5rem;text-align:center;font-size:11px;color:#40405a;font-family:Cormorant Garamond,serif;font-style:italic;line-height:1.7">'
            'Every film has a frequency.<br>Find the music that matches it.'
            '</div>',
            unsafe_allow_html=True
        )

    return movie_id, top_k, search

def render_movie_info(movie):
    section_header("Section — 02", "Movie <em style='color:#f0c060'>Context</em>",
                   accent="#d4a843")

    genre    = movie.get("genre", "")
    vote = movie.get("vote_avg") or 0
    overview = movie.get("overview", "")

    st.markdown(
        '<div style="background:#11121f;border:1px solid rgba(255,255,255,0.07);padding:1.5rem;margin-bottom:1.5rem">'

        # ชื่อหนัง
        '<div style="font-family:Cormorant Garamond,serif;font-size:1.4rem;font-weight:700;color:#fff;margin-bottom:0.8rem">'
        + movie.get("title","") + '</div>'

        # genre badge + vote
        '<div style="display:flex;gap:10px;align-items:center;margin-bottom:1rem">'
        '<span style="padding:3px 10px;font-size:10px;font-family:JetBrains Mono,monospace;'
        'border:1px solid rgba(212,168,67,0.4);background:rgba(212,168,67,0.08);color:#d4a843">'
        + genre + '</span>'
        '<span style="font-family:JetBrains Mono,monospace;font-size:11px;color:#f0c060">'
        + "{:.1f} ★".format(vote) + '</span>'
        '</div>'

        # overview
        '<div style="font-size:13px;color:#7070a0;line-height:1.8;font-weight:300">'
        + overview + '</div>'

        '</div>',
        unsafe_allow_html=True
    )

# ── RESULTS ──────────────────────────────────────────────────────────────────
def render_results(matches, title):
    section_header("Section — 02", "Vibe Matches for <em style='color:#f0c060'>" + title + "</em>",
                   "pgvector cosine similarity · top " + str(len(matches)) + " results", "#3ecfcf")

    accents = ["#d4a843","#3ecfcf","#9b72e8","#e05878","#3ecf8e"]

    # Header row
    st.markdown(
        '<div style="display:grid;grid-template-columns:36px 1fr 160px 180px;gap:12px;'
        'padding:8px 16px;background:#161728;border:1px solid rgba(255,255,255,0.07);margin-top:0.5rem">'
        '<div style="font-family:JetBrains Mono,monospace;font-size:9px;letter-spacing:2px;text-transform:uppercase;color:#40405a">#</div>'
        '<div style="font-family:JetBrains Mono,monospace;font-size:9px;letter-spacing:2px;text-transform:uppercase;color:#7070a0">Song</div>'
        '<div style="font-family:JetBrains Mono,monospace;font-size:9px;letter-spacing:2px;text-transform:uppercase;color:#7070a0">Artist</div>'
        '<div style="font-family:JetBrains Mono,monospace;font-size:9px;letter-spacing:2px;text-transform:uppercase;color:#7070a0">Vibe Score</div>'
        '</div>',
        unsafe_allow_html=True
    )

    for i, m in enumerate(matches):
        score   = m.get("similarity_score", m.get("score", 0.0))
        stitle  = m.get("song_title", m.get("title", "Track " + str(i+1)))
        artist  = m.get("artist", "Unknown")
        accent  = accents[i % len(accents)]
        pct     = int(score * 100)

        score_bar = (
            '<div style="display:flex;align-items:center;gap:8px">'
            '<div style="flex:1;height:4px;background:rgba(255,255,255,0.06);border-radius:2px;overflow:hidden;min-width:80px">'
            '<div style="width:' + str(pct) + '%;height:100%;background:' + accent + ';border-radius:2px"></div>'
            '</div>'
            '<span style="font-family:JetBrains Mono,monospace;font-size:12px;color:' + accent + ';font-weight:600;min-width:40px">'
            + "{:.3f}".format(score) + '</span>'
            '</div>'
        )

        row = (
            '<div style="display:grid;grid-template-columns:36px 1fr 160px 180px;gap:12px;align-items:center;'
            'padding:12px 16px;background:#11121f;border:1px solid rgba(255,255,255,0.07);border-top:none;align-items:start;'
            'border-left:3px solid ' + accent + '">'
            '<div style="font-family:JetBrains Mono,monospace;font-size:11px;color:#40405a;font-weight:600">'
            + "{:02d}".format(i+1) + '</div>'
            '<div>'
                '<div style="font-size:14px;font-weight:500;color:#eeeef5">' + stitle + '</div>'
                '<div style="margin-top:6px;display:flex;align-items:center;gap:6px">'
                '<span style="font-size:9px;color:#7070a0;font-family:JetBrains Mono,monospace;width:52px">content</span>'
                '<div style="flex:1;height:3px;background:rgba(255,255,255,0.06);border-radius:2px;max-width:80px">'
                '<div style="width:' + str(int(m.get("content_score",0)*100)) + '%;height:100%;background:#3ecfcf;border-radius:2px"></div>'
                '</div>'
                '<span style="font-size:9px;color:#3ecfcf;font-family:JetBrains Mono,monospace">' + "{:.2f}".format(m.get("content_score",0)) + '</span>'
                '</div>'
                '<div style="margin-top:3px;display:flex;align-items:center;gap:6px">'
                '<span style="font-size:9px;color:#7070a0;font-family:JetBrains Mono,monospace;width:52px">audio</span>'
                '<div style="flex:1;height:3px;background:rgba(255,255,255,0.06);border-radius:2px;max-width:80px">'
                '<div style="width:' + str(int(m.get("audio_score",0)*100)) + '%;height:100%;background:#9b72e8;border-radius:2px"></div>'
                '</div>'
                '<span style="font-size:9px;color:#9b72e8;font-family:JetBrains Mono,monospace">' + "{:.2f}".format(m.get("audio_score",0)) + '</span>'
                '</div>'
            '</div>'
            '<div style="font-size:13px;color:#7070a0">' + artist + '</div>'
            + score_bar +
            '</div>'
        )
        st.markdown(row, unsafe_allow_html=True)

    # Chart
    st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)
    section_header("Visualization", "Score Distribution", accent="#9b72e8")
    try:
        import plotly.graph_objects as go
        titles = [m.get("song_title", "Track " + str(i+1)) for i, m in enumerate(matches)]
        scores = [m.get("similarity_score", 0.0) for m in matches]
        colors = [accents[i % len(accents)] for i in range(len(matches))]
        fig = go.Figure(go.Bar(x=scores, y=titles, orientation="h",
            marker=dict(color=colors, opacity=0.85),
            text=["{:.3f}".format(s) for s in scores], textposition="outside",
            textfont=dict(family="JetBrains Mono", size=11, color="#7070a0")))
        fig.update_layout(
            paper_bgcolor="#11121f", plot_bgcolor="#11121f",
            font=dict(family="Outfit", color="#7070a0", size=12),
            xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)",
                       tickfont=dict(family="JetBrains Mono", size=10), range=[0,1.1], zeroline=False),
            yaxis=dict(showgrid=False, tickfont=dict(family="Outfit",size=12,color="#eeeef5"), autorange="reversed"),
            margin=dict(l=0, r=60, t=10, b=10), height=max(200, len(matches)*46), bargap=0.35)
        st.plotly_chart(fig, width='stretch')
    except ImportError:
        pass

# ── FEEDBACK ─────────────────────────────────────────────────────────────────
def render_feedback(movie_id, matches):
    section_header("Section — 03", "Rate This <em style='color:#f0c060'>Match</em>",
                   "Feedback ช่วย improve embeddings", "#e05878")
    if not matches:
        return
    c1, c2 = st.columns(2, gap="large")
    with c1:
        st.markdown('<div style="font-family:JetBrains Mono,monospace;font-size:10px;letter-spacing:2px;text-transform:uppercase;color:#7070a0;margin-bottom:6px">Select Song</div>', unsafe_allow_html=True)
        song_opts = {m.get("song_title","Track "+str(i+1)): m.get("song_id",i+1) for i,m in enumerate(matches)}
        sel_song  = st.selectbox("song", list(song_opts.keys()), label_visibility="collapsed")
        song_id   = song_opts[sel_song]
        st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)
        st.markdown('<div style="font-family:JetBrains Mono,monospace;font-size:10px;letter-spacing:2px;text-transform:uppercase;color:#7070a0;margin-bottom:6px">Rating</div>', unsafe_allow_html=True)
        stars = ["★☆☆☆☆  Mismatched","★★☆☆☆  Weak","★★★☆☆  Fair","★★★★☆  Good","★★★★★  Perfect"]
        rating_label = st.radio("rating", stars, index=2, label_visibility="collapsed")
        rating_val   = stars.index(rating_label) + 1
    with c2:
        st.markdown('<div style="font-family:JetBrains Mono,monospace;font-size:10px;letter-spacing:2px;text-transform:uppercase;color:#7070a0;margin-bottom:6px">Notes</div>', unsafe_allow_html=True)
        note = st.text_area("note", placeholder="Why does this match (or not)?", height=100, label_visibility="collapsed")
        st.markdown("<div style='height:0.6rem'></div>", unsafe_allow_html=True)
        if st.button("Submit Feedback"):
            ok = post_feedback(movie_id, song_id, rating_val, note)
            if ok:
                st.success("Feedback recorded!")
            else:
                st.warning("API offline — logged locally")

# ── WELCOME ──────────────────────────────────────────────────────────────────
def render_welcome():
    section_header("Section — 01", "How It <em style='color:#f0c060'>Works</em>", accent="#3ecfcf")
    c1, c2, c3 = st.columns(3, gap="small")
    for col, (color, num, title, desc) in zip([c1,c2,c3],[
        ("#d4a843","01","Select a Film",  "เลือกหนังจาก sidebar — ระบบ generate embedding จาก TMDB metadata"),
        ("#3ecfcf","02","Vector Search",  "pgvector cosine similarity เปรียบเทียบ film กับ song embeddings"),
        ("#9b72e8","03","Discover Vibes", "ได้ top-K songs ที่ vibe ใกล้เคียงที่สุด — rating ช่วย retrain model"),
    ]):
        with col:
            st.markdown(
                '<div style="background:#11121f;border:1px solid rgba(255,255,255,0.07);border-top:3px solid ' + color + ';padding:1.5rem;min-height:160px">'
                '<div style="font-family:JetBrains Mono,monospace;font-size:1.6rem;font-weight:600;color:' + color + ';opacity:0.3;margin-bottom:0.8rem">' + num + '</div>'
                '<div style="font-size:14px;font-weight:600;color:#fff;margin-bottom:0.5rem">' + title + '</div>'
                '<div style="font-size:12px;color:#7070a0;line-height:1.7;font-weight:300">' + desc + '</div>'
                '</div>',
                unsafe_allow_html=True
            )

# ── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    st.markdown(CSS, unsafe_allow_html=True)

    # Vibe rotation
    if "vibe_idx"      not in st.session_state: st.session_state.vibe_idx = 0
    if "last_rotate"   not in st.session_state: st.session_state.last_rotate = time.time()
    now = time.time()
    if now - st.session_state.last_rotate > 3.5:
        st.session_state.vibe_idx = (st.session_state.vibe_idx + 1) % len(DEMO_VIBES)
        st.session_state.last_rotate = now

    render_hero(DEMO_VIBES[st.session_state.vibe_idx])

    movies, offline = fetch_movies()
    movie_id, top_k, search = render_sidebar(movies, offline)
    movie_title = next((m["title"] for m in movies if m["id"] == movie_id), "Film")

    if "results" not in st.session_state: st.session_state.results = None
    if "rtitle"  not in st.session_state: st.session_state.rtitle  = ""
    if "rmovie"  not in st.session_state: st.session_state.rmovie  = None
    if "rmovie_data" not in st.session_state: st.session_state.rmovie_data = None

    if search:
        matches, _ = fetch_recommendations(movie_id, top_k)
        st.session_state.results = matches
        st.session_state.rtitle  = movie_title
        st.session_state.rmovie  = movie_id
        st.session_state.rmovie_data = next((m for m in movies if m["id"] == movie_id), None)

    if st.session_state.results:
        if st.session_state.rmovie_data:
            render_movie_info(st.session_state.rmovie_data)
        render_results(st.session_state.results, st.session_state.rtitle)
        st.markdown("<div style='height:2rem'></div>", unsafe_allow_html=True)
        render_feedback(st.session_state.rmovie, st.session_state.results)
    else:
        render_welcome()

    # Footer
    st.markdown(
        '<div style="margin-top:4rem;padding:2rem 0 1.5rem;border-top:1px solid rgba(255,255,255,0.07);text-align:center">'
        '<div style="font-family:Cormorant Garamond,serif;font-style:italic;font-size:1rem;color:#40405a">'
        'Every film has a frequency. Find the music that matches it.</div>'
        '</div>',
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
