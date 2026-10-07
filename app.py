import os
import random
from html import escape

import requests
import streamlit as st

# ------------------------------------------------------------------
# CONFIG
# ------------------------------------------------------------------
API_BASE = os.getenv("API_BASE", "http://127.0.0.1:8000")
CATEGORIES = {
    "Trending": "trending",
    "Popular": "popular",
    "Top rated": "top_rated",
    "Coming soon": "upcoming",
    "In theatres": "now_playing",
}
PLACEHOLDER = "https://placehold.co/500x750/2A1B3D/F3E3C3?text=No+Poster"

st.set_page_config(page_title="MovieMania | Find your next watch", page_icon="🎟️", layout="wide")

# ------------------------------------------------------------------
# STYLE: "projector room" - ink + plum curtains, amber marquee, cream ticket stubs
# ------------------------------------------------------------------
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Limelight&family=DM+Sans:wght@400;500;700&display=swap');
:root{--ink:#14101F;--plum:#2A1B3D;--cream:#F3E3C3;--amber:#FFB627;--rose:#E8456B;--mute:#A99BBE;}
html,body,[class*="css"],.stApp{font-family:'DM Sans',sans-serif;color:var(--cream);}
.stApp{background:radial-gradient(1200px 500px at 50% -10%,#3b2457 0%,var(--ink) 60%) fixed;}
#MainMenu,footer,header[data-testid="stHeader"]{visibility:hidden;height:0;}
.block-container{padding-top:1.2rem;max-width:1300px;}

/* brand bar */
.brand{display:flex;align-items:center;gap:14px;margin-bottom:.2rem;}
.logo{font-family:'Limelight',serif;font-size:2.4rem;color:var(--amber);letter-spacing:2px;
 text-shadow:0 0 6px rgba(255,182,39,.8),0 0 22px rgba(255,182,39,.35);}
.bulbs{height:10px;margin:2px 0 14px;background:radial-gradient(circle,var(--amber) 3px,transparent 4px) 0 0/22px 10px repeat-x;opacity:.85;}
.tag{color:var(--mute);font-size:.95rem;margin-left:auto;}

/* nav radio -> pills */
div[role="radiogroup"]{gap:.4rem;flex-wrap:wrap;}
div[role="radiogroup"] label{background:var(--plum);border:1px solid #4a3367;border-radius:999px;padding:.25rem 1rem;}
div[role="radiogroup"] label:has(input:checked){background:var(--amber);border-color:var(--amber);}
div[role="radiogroup"] label:has(input:checked) p{color:var(--ink)!important;font-weight:700;}
div[role="radiogroup"] label>div:first-child{display:none;}

/* hero */
.hero{position:relative;border-radius:22px;overflow:hidden;min-height:340px;padding:2.4rem;display:flex;align-items:flex-end;
 background-size:cover;background-position:center 20%;border:1px solid #4a3367;}
.hero h1{font-family:'Limelight',serif;font-size:3rem;margin:0 0 .4rem;color:var(--cream);line-height:1.05;}
.hero p{max-width:620px;color:#e5d6bb;margin:0;}
.hero .kick{color:var(--amber);font-weight:700;margin-bottom:.5rem;}

/* ticket-stub card */
.stub{background:var(--cream);color:var(--ink);border-radius:14px;overflow:hidden;position:relative;
 transition:transform .18s ease, box-shadow .18s ease;box-shadow:0 8px 20px rgba(0,0,0,.35);}
.stub:hover{transform:translateY(-6px) rotate(-.6deg);box-shadow:0 16px 30px rgba(255,182,39,.25);}
.stub img{width:100%;aspect-ratio:2/3;object-fit:cover;display:block;}
.stub .rate{position:absolute;top:8px;right:8px;background:var(--ink);color:var(--amber);font-weight:700;
 border-radius:999px;padding:2px 10px;font-size:.8rem;border:1px solid var(--amber);}
.stub .perf{border-top:3px dashed #14101F55;margin:0 10px;}
.stub .info{padding:.5rem .7rem .6rem;}
.stub .t{font-weight:700;font-size:.9rem;line-height:1.2;height:2.2em;overflow:hidden;}
.stub .y{font-size:.75rem;color:#6b5a85;}
.stub .match{height:6px;background:#14101F22;border-radius:6px;margin-top:6px;overflow:hidden;}
.stub .match i{display:block;height:100%;background:linear-gradient(90deg,var(--rose),var(--amber));}
.stub .mt{font-size:.7rem;color:#6b5a85;margin-top:2px;}

/* buttons */
.stButton>button{width:100%;background:transparent;color:var(--amber);border:1px solid var(--amber);border-radius:10px;font-weight:700;}
.stButton>button:hover{background:var(--amber);color:var(--ink);border-color:var(--amber);}
.stTextInput input{background:var(--plum);color:var(--cream);border:1px solid #4a3367;border-radius:12px;}

/* detail */
.chip{display:inline-block;background:var(--plum);border:1px solid var(--amber);color:var(--amber);border-radius:999px;
 padding:2px 12px;margin:0 6px 6px 0;font-size:.85rem;}
.sec{font-family:'Limelight',serif;font-size:1.6rem;color:var(--amber);margin:1.6rem 0 .6rem;}
.empty{border:2px dashed #4a3367;border-radius:16px;padding:2rem;text-align:center;color:var(--mute);}
.stTabs [data-baseweb="tab"]{color:var(--mute);} .stTabs [aria-selected="true"]{color:var(--amber)!important;}
</style>
""",
    unsafe_allow_html=True,
)

# ------------------------------------------------------------------
# API HELPERS
# ------------------------------------------------------------------
@st.cache_data(ttl=300, show_spinner=False)
def api(path: str, params: tuple = ()):
    try:
        r = requests.get(f"{API_BASE}{path}", params=dict(params), timeout=40)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"__error__": str(e)}


def failed(data) -> bool:
    return isinstance(data, dict) and "__error__" in data


def normalize(m: dict) -> dict:
    """Accept both our card shape and raw TMDB search shape."""
    if "tmdb_id" in m:
        return m
    p = m.get("poster_path")
    return {
        "tmdb_id": m.get("id"),
        "title": m.get("title") or m.get("name") or "",
        "poster_url": f"https://image.tmdb.org/t/p/w500{p}" if p else None,
        "release_date": m.get("release_date"),
        "vote_average": m.get("vote_average"),
    }


# ------------------------------------------------------------------
# STATE
# ------------------------------------------------------------------
st.session_state.setdefault("detail_id", None)
st.session_state.setdefault("watchlist", {})
st.session_state.setdefault("category", "Trending")


def open_movie(tmdb_id: int):
    st.session_state.detail_id = tmdb_id


def close_movie():
    st.session_state.detail_id = None


def surprise():
    data = api("/home", (("category", "popular"), ("limit", 50)))
    if not failed(data) and data:
        st.session_state.detail_id = random.choice(data)["tmdb_id"]


def toggle_watch(movie: dict):
    wl = st.session_state.watchlist
    if movie["tmdb_id"] in wl:
        wl.pop(movie["tmdb_id"])
    else:
        wl[movie["tmdb_id"]] = movie


# ------------------------------------------------------------------
# UI COMPONENTS
# ------------------------------------------------------------------
def stub_html(m: dict, score: float | None = None) -> str:
    year = (m.get("release_date") or "")[:4] or "TBA"
    rating = m.get("vote_average")
    rate = f'<div class="rate">★ {rating:.1f}</div>' if rating else ""
    match = ""
    if score is not None:
        pct = max(0, min(100, round(score * 100)))
        match = f'<div class="match"><i style="width:{pct}%"></i></div><div class="mt">{pct}% story match</div>'
    return (
        f'<div class="stub">{rate}<img src="{m.get("poster_url") or PLACEHOLDER}" loading="lazy"/>'
        f'<div class="perf"></div><div class="info"><div class="t">{escape(m["title"])}</div>'
        f'<div class="y">{year}</div>{match}</div></div>'
    )


def grid(movies: list, prefix: str, cols: int = 6, scores: dict | None = None):
    movies = [normalize(m) for m in movies if m]
    if not movies:
        st.markdown('<div class="empty">Nothing on screen here yet.</div>', unsafe_allow_html=True)
        return
    for row_start in range(0, len(movies), cols):
        row = movies[row_start : row_start + cols]
        cs = st.columns(cols)
        for i, m in enumerate(row):
            with cs[i]:
                sc = (scores or {}).get(m["tmdb_id"])
                st.markdown(stub_html(m, sc), unsafe_allow_html=True)
                st.button("Details", key=f"{prefix}_{m['tmdb_id']}_{row_start + i}",
                          on_click=open_movie, args=(m["tmdb_id"],))
        st.write("")


def hero(title, overview, backdrop, kicker):
    overview = escape((overview or "")[:260]) + ("…" if overview and len(overview) > 260 else "")
    bg = (f"linear-gradient(90deg,rgba(20,16,31,.95) 20%,rgba(20,16,31,.25)),url('{backdrop}')"
          if backdrop else "linear-gradient(135deg,#2A1B3D,#14101F)")
    st.markdown(
        f'<div class="hero" style="background-image:{bg}"><div><div class="kick">{kicker}</div>'
        f'<h1>{escape(title)}</h1><p>{overview}</p></div></div>',
        unsafe_allow_html=True,
    )


# ------------------------------------------------------------------
# PAGES
# ------------------------------------------------------------------
def page_home():
    cat = st.radio("Category", list(CATEGORIES), horizontal=True, key="category", label_visibility="collapsed")
    data = api("/home", (("category", CATEGORIES[cat]), ("limit", 24)))
    if failed(data):
        st.error(f"Can't reach the MovieMania API at {API_BASE}. Start it with `uvicorn main:app --reload`.")
        return
    if data:
        top = api(f"/movie/id/{data[0]['tmdb_id']}")
        if not failed(top):
            hero(top["title"], top.get("overview"), top.get("backdrop_url"), f"Now showing in {cat.lower()}")
            st.write("")
            st.button("Open this film", on_click=open_movie, args=(top["tmdb_id"],), key="hero_btn")
    st.markdown(f'<div class="sec">{cat}</div>', unsafe_allow_html=True)
    grid(data, "home")


def page_search():
    q = st.text_input("Search", placeholder="Type a movie you love, e.g. Inception", label_visibility="collapsed")
    if not q:
        st.markdown('<div class="empty">Type a title you loved. We will find films that feel like it.</div>',
                    unsafe_allow_html=True)
        return
    data = api("/tmdb/search", (("query", q),))
    if failed(data):
        st.error("Search failed. Check that the API is running and try again.")
        return
    results = data.get("results", [])
    if not results:
        st.markdown(f'<div class="empty">No films match “{escape(q)}”. Try a shorter title.</div>',
                    unsafe_allow_html=True)
        return
    st.markdown(f'<div class="sec">Results for “{escape(q)}”</div>', unsafe_allow_html=True)
    grid(results[:18], "search")


def page_watchlist():
    wl = list(st.session_state.watchlist.values())
    st.markdown('<div class="sec">Your watchlist</div>', unsafe_allow_html=True)
    if not wl:
        st.markdown('<div class="empty">Your watchlist is empty. Open any film and tap “Add to watchlist”.</div>',
                    unsafe_allow_html=True)
        return
    grid(wl, "wl")


def page_detail(tmdb_id: int):
    st.button("← Back", on_click=close_movie, key="back")
    d = api(f"/movie/id/{tmdb_id}")
    if failed(d):
        st.error("Could not load this movie.")
        return
    hero(d["title"], None, d.get("backdrop_url"), (d.get("release_date") or "")[:4] or "Release date TBA")
    st.write("")
    c1, c2 = st.columns([1, 3])
    card = {"tmdb_id": d["tmdb_id"], "title": d["title"], "poster_url": d.get("poster_url"),
            "release_date": d.get("release_date"), "vote_average": None}
    with c1:
        st.markdown(stub_html(card), unsafe_allow_html=True)
    with c2:
        st.markdown("".join(f'<span class="chip">{escape(g["name"])}</span>' for g in d.get("genres", [])),
                    unsafe_allow_html=True)
        st.write(d.get("overview") or "No synopsis available.")
        saved = d["tmdb_id"] in st.session_state.watchlist
        st.button("Remove from watchlist" if saved else "Add to watchlist",
                  on_click=toggle_watch, args=(card,), key="watch_btn")

    with st.spinner("Rolling the reels for similar films…"):
        bundle = api("/movie/search", (("query", d["title"]), ("tfidf_top_n", 12), ("genre_limit", 12)))
    if failed(bundle):
        st.warning("Recommendations are unavailable right now.")
        return

    t1, t2 = st.tabs(["Similar story (AI)", "Same genre"])
    with t1:
        recs = bundle.get("tfidf_recommendations", [])
        items, scores = [], {}
        for r in recs:
            if r.get("tmdb"):
                items.append(r["tmdb"])
                scores[r["tmdb"]["tmdb_id"]] = r["score"]
        if items:
            st.caption("Ranked by how closely each plot and theme matches, using TF-IDF similarity.")
            grid(items, "ai", scores=scores)
        else:
            st.markdown('<div class="empty">This title is not in our recommendation dataset yet. '
                        'Try the Same genre tab.</div>', unsafe_allow_html=True)
    with t2:
        grid(bundle.get("genre_recommendations", []), "genre")


# ------------------------------------------------------------------
# LAYOUT
# ------------------------------------------------------------------
st.markdown(
    '<div class="brand"><span class="logo">MOVIEMANIA</span>'
    '<span class="tag">Tell us one film you love. We pick the next.</span></div><div class="bulbs"></div>',
    unsafe_allow_html=True,
)

nav_col, surprise_col = st.columns([5, 1])
with nav_col:
    page = st.radio("Navigate", ["Home", "Search", "Watchlist"], horizontal=True,
                    label_visibility="collapsed", on_change=close_movie, key="nav")
with surprise_col:
    st.button("🎲 Surprise me", on_click=surprise, key="surprise")

st.write("")
if st.session_state.detail_id:
    page_detail(st.session_state.detail_id)
elif page == "Home":
    page_home()
elif page == "Search":
    page_search()
else:
    page_watchlist()