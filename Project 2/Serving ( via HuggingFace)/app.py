from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel
import boto3, pickle, io, os, json
import pandas as pd

app = FastAPI()

s3 = boto3.client(
    "s3",
    aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
    aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
    region_name=os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
)

BUCKET = "nbapredictions-sthomas26-ncf"
SEASON = "2024-25"

# Load model
buf = io.BytesIO()
s3.download_fileobj(BUCKET, "model/nba_model.pkl", buf)
buf.seek(0)
model = pickle.load(buf)

# Load gold data and compute per-team averages
def load_team_stats():
    resp = s3.list_objects_v2(Bucket=BUCKET, Prefix=f"gold/games/season={SEASON}/")
    frames = []
    for obj in resp["Contents"]:
        key = obj["Key"]
        if key.endswith(".parquet"):
            buf2 = io.BytesIO()
            s3.download_fileobj(BUCKET, key, buf2)
            buf2.seek(0)
            frames.append(pd.read_parquet(buf2))
    df = pd.concat(frames)

    # Get each team's most recent rolling averages
    latest = df.sort_values("GAME_DATE").groupby("TEAM_ABBREVIATION").last().reset_index()
    stats = {}
    for _, row in latest.iterrows():
        stats[row["TEAM_ABBREVIATION"]] = {
            "AVG_PTS_L10":        row["AVG_PTS_L10"],
            "AVG_REB_L10":        row["AVG_REB_L10"],
            "AVG_AST_L10":        row["AVG_AST_L10"],
            "AVG_TOV_L10":        row["AVG_TOV_L10"],
            "AVG_PLUS_MINUS_L10": row["AVG_PLUS_MINUS_L10"],
            "REST_DAYS":          float(row["REST_DAYS"]) if pd.notna(row["REST_DAYS"]) else 2.0,
        }
    return stats

# Load on startup
team_stats = load_team_stats()
print(f"Loaded stats for {len(team_stats)} teams: {list(team_stats.keys())}")

FEATURES = ["HOME", "REST_DAYS", "AVG_PTS_L10", "AVG_REB_L10",
            "AVG_AST_L10", "AVG_TOV_L10", "AVG_PLUS_MINUS_L10"]

# Fallback league averages if team not found
LEAGUE_AVG = {
    "AVG_PTS_L10": 112.0, "AVG_REB_L10": 44.0, "AVG_AST_L10": 26.0,
    "AVG_TOV_L10": 14.0, "AVG_PLUS_MINUS_L10": 0.0, "REST_DAYS": 2.0
}

class PredictRequest(BaseModel):
    home_team: str
    away_team: str

@app.get("/")
def root():
    return FileResponse("index.html")

@app.get("/teams")
def get_teams():
    return {"teams": sorted(list(team_stats.keys()))}

@app.get("/debug")
def debug():
    return {
        "teams_loaded": sorted(list(team_stats.keys())),
        "sample_LAL": team_stats.get("LAL", "NOT FOUND"),
        "sample_BOS": team_stats.get("BOS", "NOT FOUND"),
    }

@app.post("/predict")
def predict(req: PredictRequest):
    home = team_stats.get(req.home_team, LEAGUE_AVG)
    away = team_stats.get(req.away_team, LEAGUE_AVG)

    home_row = [[
        1,
        home["REST_DAYS"],
        home["AVG_PTS_L10"],
        home["AVG_REB_L10"],
        home["AVG_AST_L10"],
        home["AVG_TOV_L10"],
        home["AVG_PLUS_MINUS_L10"],
    ]]

    away_row = [[
        0,
        away["REST_DAYS"],
        away["AVG_PTS_L10"],
        away["AVG_REB_L10"],
        away["AVG_AST_L10"],
        away["AVG_TOV_L10"],
        away["AVG_PLUS_MINUS_L10"],
    ]]

    home_prob = float(model.predict_proba(home_row)[0][1])
    away_prob = float(model.predict_proba(away_row)[0][1])

    # Normalize so they add to 100
    total = home_prob + away_prob
    home_pct = round((home_prob / total) * 100, 1)
    away_pct = round((away_prob / total) * 100, 1)

    return {
        "home_team": req.home_team,
        "away_team": req.away_team,
        "home_win_prob": home_pct,
        "away_win_prob": away_pct
    }