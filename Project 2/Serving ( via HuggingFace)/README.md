# Serving

FastAPI application that loads the trained XGBoost model from S3 and exposes a REST prediction endpoint. Deployed on Hugging Face Spaces via Docker.

---

## Files

| File | Description |
|------|-------------|
| `app.py` | FastAPI app — loads model + gold layer stats on startup, serves /predict |
| `requirements.txt` | Python dependencies |
| `Dockerfile` | Container config for Hugging Face Spaces (port 7860) |

---

## Endpoints

| Method | Route | Description |
|--------|-------|-------------|
| GET | `/` | Serves the frontend UI (index.html) |
| GET | `/teams` | Returns list of all teams with loaded stats |
| GET | `/debug` | Returns sample team stats for debugging |
| POST | `/predict` | Returns win probabilities for a matchup |

---

## POST /predict

**Request body:**
```json
{
  "home_team": "LAL",
  "away_team": "BOS"
}
```

**Response:**
```json
{
  "home_team": "LAL",
  "away_team": "BOS",
  "home_win_prob": 43.2,
  "away_win_prob": 56.8
}
```

---

## How It Works

On startup the app:
1. Connects to S3 using credentials stored as Hugging Face Space secrets
2. Downloads `model/nba_model.pkl` — the serialized XGBoost classifier
3. Reads all Parquet files from `gold/games/season=2024-25/`
4. Groups by team and takes each team's most recent rolling averages as their current stats

On each `/predict` request:
1. Looks up the home and away team stats from the preloaded dictionary
2. Builds a feature vector for each team (HOME flag + 6 rolling stats)
3. Runs both through the model and normalizes probabilities to sum to 100%
4. Returns the result as JSON

---

## Deployment (Hugging Face Spaces)

1. Create a new Space on huggingface.co with SDK set to **Docker**
2. Upload `app.py`, `requirements.txt`, `Dockerfile`, and `../frontend/index.html`
3. Add the following as **Space Secrets** (Settings → Repository secrets):
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
   - `AWS_DEFAULT_REGION` → `us-east-1`
4. The Space builds automatically — logs are visible in the Logs tab

---

## Running Locally

```bash
pip install -r requirements.txt

export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_DEFAULT_REGION=us-east-1

uvicorn app:app --host 0.0.0.0 --port 8000
```

Then visit `http://localhost:8000/docs` for the interactive API docs.
