# NBA Win Predictor

A distributed machine learning pipeline that predicts NBA game win probabilities using historical team performance data.

**Live Demo:** https://sthomas10-nba-predictor.hf.space/

---

## Overview

Given a home and away team, the system returns real-time win probabilities based on each team's rolling 10-game performance averages, home-court advantage, and rest days. The full pipeline follows a medallion architecture (Bronze → Silver → Gold) with data stored on Amazon S3, transformations run on Databricks, and the model tracked in MLflow.

---

## Architecture

```
NBA Stats API
     ↓
Bronze Layer (S3) — raw JSON game logs + team metrics
     ↓
Silver Layer (S3 Parquet) — cleaned, typed data via PySpark
     ↓
Gold Layer (S3 Parquet) — feature-engineered, model-ready data
     ↓
MLflow (Databricks) — XGBoost training, experiment tracking
     ↓
FastAPI (Hugging Face Spaces) — REST prediction endpoint
     ↓
HTML/CSS/JS Frontend — live win probability UI
```

---

## Tech Stack

| Layer | Tool |
|-------|------|
| Data ingestion | Python, nba_api, boto3 |
| Cloud storage | Amazon S3 |
| Data transformation | PySpark, Databricks Community Edition |
| ML training | XGBoost, scikit-learn, MLflow |
| Model serving | FastAPI, Docker |
| Deployment | Hugging Face Spaces |
| Frontend | HTML, CSS, JavaScript |

---

## Model Performance

| Metric | Value |
|--------|-------|
| Accuracy | 58.5% |
| AUC-ROC | 0.633 |
| Algorithm | XGBoost |
| Train/Test Split | 80% / 20% |
| Season | 2024-25 NBA |

Accuracy exceeds the 50% random baseline, consistent with published NBA prediction benchmarks (55–65% range).

---

## Features Used

| Feature | Description |
|---------|-------------|
| HOME | 1 if home team, 0 if away |
| REST_DAYS | Days since last game |
| AVG_PTS_L10 | Average points over last 10 games |
| AVG_REB_L10 | Average rebounds over last 10 games |
| AVG_AST_L10 | Average assists over last 10 games |
| AVG_TOV_L10 | Average turnovers over last 10 games |
| AVG_PLUS_MINUS_L10 | Average plus/minus over last 10 games |

---

## Repository Structure

```
nba-win-predictor/
├── README.md
├── test_project.py               # Endpoint test script
├── notebooks/
│   ├── 01_bronze_ingestion.ipynb # Pull NBA data → S3
│   ├── 02_silver.ipynb           # PySpark cleaning → S3 Parquet
│   ├── 03_gold.ipynb             # Feature engineering → S3 Parquet
│   └── 04_ml_training.ipynb      # XGBoost training + MLflow logging
├── serving/
│   ├── app.py                    # FastAPI prediction endpoint
│   ├── requirements.txt          # Python dependencies
│   └── Dockerfile                # Container config
└── frontend/
    └── index.html                # Web UI
```

---

## API Usage

**Endpoint:** `POST /predict`

**Request:**
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

## Running the Test Script

```bash
pip install requests
python test_project.py
```

Expected output:
```
✅ All tests passed.
```

---

## Setup & Reproduction

### Prerequisites
- AWS account with S3 bucket
- Databricks Community Edition account
- Hugging Face account

### 1. Bronze ingestion (Google Colab)
```bash
pip install nba_api boto3
# Set AWS credentials, run notebooks/01_bronze_ingestion.ipynb
```

### 2. Silver + Gold transformation (Databricks)
```
# Upload notebooks/02_silver.ipynb and 03_gold.ipynb to Databricks
# Attach to a running cluster and execute
```

### 3. ML training (Databricks)
```
# Run notebooks/04_ml_training.ipynb
# Model saved to s3://your-bucket/model/nba_model.pkl
```

### 4. Deploy serving endpoint (Hugging Face Spaces)
```
# Create a new Docker Space on huggingface.co
# Upload serving/app.py, serving/requirements.txt, serving/Dockerfile
# Add AWS credentials as Space secrets
```

### 5. Deploy frontend
```
# Upload frontend/index.html to the same HF Space
# Update API_URL in index.html to your Space URL
```

---

## S3 Bucket Structure

```
s3://your-bucket/
├── bronze/
│   ├── games/season=2024-25/run=TIMESTAMP/games.json
│   └── team_stats/season=2024-25/run=TIMESTAMP/team_stats.json
├── silver/
│   └── games/season=2024-25/*.parquet
├── gold/
│   └── games/season=2024-25/*.parquet
└── model/
    └── nba_model.pkl
```

---

## Author

S. Thomas — New College of Florida  
Distributed Systems for Data Science — Spring 2025
