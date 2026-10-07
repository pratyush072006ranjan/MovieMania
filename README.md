# 🎟️ MovieMania

A movie recommendation platform. Tell it one film you love and it suggests what to watch next.

MovieMania combines a **machine learning model** (TF-IDF + cosine similarity on movie text) with **live TMDB data** (posters, details, trending lists), served by a **FastAPI** backend and presented in a **Streamlit** frontend styled like a cinema marquee.

---

## Features

- **Similar story recommendations (ML):** ranks films by how closely their plots and themes match, with a match bar on every card.
- **Same genre recommendations:** popular films in the selected movie's main genre, pulled from TMDB.
- **Home feed:** Trending, Popular, Top rated, Coming soon and In theatres, with a hero banner for the top film.
- **Search:** find any movie by title and open its details.
- **Movie details page:** backdrop, poster, genres, synopsis and both recommendation tabs.
- **Watchlist:** save films during your session.
- **Surprise me:** jump to a random popular movie.

## How it works

```
Streamlit (app.py)  ──HTTP──▶  FastAPI (main.py)  ──▶  TMDB API
                                      │
                                      └──▶ TF-IDF model (pickle files)
```

1. The user opens a movie in the Streamlit app.
2. The app calls `/movie/search` on the backend.
3. The backend finds the movie on TMDB, then looks up its row in the local TF-IDF matrix and returns the most similar titles by cosine similarity.
4. Each recommended title is matched back to TMDB to fetch its poster and rating.
5. Genre-based picks come from TMDB's discover endpoint, and the app shows both sets in tabs.

## Project structure

```
.
├── app.py               # Streamlit frontend
├── main.py              # FastAPI backend
├── df.pkl               # Movie dataset (must have a 'title' column)
├── indices.pkl          # Title -> row index mapping (dict or pandas Series)
├── tfidf_matrix.pkl     # TF-IDF matrix (scipy sparse)
├── tfidf.pkl            # Fitted TF-IDF vectorizer
├── .env                 # Your TMDB API key (not committed)
└── requirements.txt
```

## Setup

### 1. Prerequisites

- Python 3.10 or newer
- A free [TMDB API key](https://www.themoviedb.org/settings/api)
- The four `.pkl` files from your model training, placed next to `main.py`

### 2. Install dependencies

Create a `requirements.txt`:

```
fastapi
uvicorn
httpx
pandas
numpy
scipy
scikit-learn
pydantic
python-dotenv
streamlit
requests
```

Then install:

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

> Use the same `scikit-learn` and `pandas` versions you trained with, or the pickle files may fail to load.

### 3. Add your TMDB key

Create a `.env` file in the project root:

```
TMDB_API_KEY=your_key_here
```

### 4. Run it

Open two terminals.

**Terminal 1: backend**
```bash
uvicorn main:app --reload
```
The API runs at `http://127.0.0.1:8000`, and interactive docs are at `/docs`.

**Terminal 2: frontend**
```bash
streamlit run app.py
```
The app opens at `http://localhost:8501`.

If your backend runs somewhere else, set the address before starting Streamlit:

```bash
API_BASE=http://your-host:8000 streamlit run app.py
```

## API endpoints

| Endpoint | Description |
|---|---|
| `GET /health` | Health check |
| `GET /home?category=&limit=` | Home feed. Categories: `trending`, `popular`, `top_rated`, `upcoming`, `now_playing` |
| `GET /tmdb/search?query=&page=` | Keyword search, returns raw TMDB results |
| `GET /movie/id/{tmdb_id}` | Movie details |
| `GET /recommend/genre?tmdb_id=&limit=` | Genre-based recommendations |
| `GET /recommend/tfidf?title=&top_n=` | TF-IDF recommendations only (useful for debugging) |
| `GET /movie/search?query=&tfidf_top_n=&genre_limit=` | Bundle: details + TF-IDF picks + genre picks |

## Troubleshooting

**"Can't reach the MovieMania API"**
The backend isn't running or `API_BASE` is wrong. Start `uvicorn` first and check `http://127.0.0.1:8000/health`.

**`TMDB_API_KEY missing`**
The `.env` file is missing or not in the folder you launch `uvicorn` from.

**Pickle load errors on startup**
Check that all four `.pkl` files sit next to `main.py`, and that your library versions match the ones used for training.

**"This title is not in our recommendation dataset yet"**
The movie exists on TMDB but not in your local `df.pkl`, so there are no ML picks for it. The genre tab still works.

**First movie page loads slowly**
Each recommendation needs its own TMDB lookup for a poster. Results are cached for 5 minutes, so repeat visits are fast.

## Ideas for next steps

- Mood-based discovery (cozy, intense, mind-bending)
- Persistent watchlists with user accounts
- Cache poster lookups in the backend to speed up recommendations
- Combine several liked movies into one recommendation
- Restrict CORS `allow_origins` before deploying publicly

## Credits

This product uses the TMDB API but is not endorsed or certified by TMDB. Movie data and images are provided by [The Movie Database](https://www.themoviedb.org/).
