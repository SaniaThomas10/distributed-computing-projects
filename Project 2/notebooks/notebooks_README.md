# Notebooks

Four notebooks that implement the full medallion pipeline from raw NBA API data to a trained, saved ML model. Run them in order.

---

## Execution Order

| # | Notebook | Platform | Output |
|---|----------|----------|--------|
| 1 | `01_bronze_ingestion.ipynb` | Google Colab | Raw JSON in S3 bronze/ |
| 2 | `02_silver.ipynb` | Databricks | Cleaned Parquet in S3 silver/ |
| 3 | `03_gold.ipynb` | Databricks | Feature-engineered Parquet in S3 gold/ |
| 4 | `04_ml_training.ipynb` | Databricks | Trained model in S3 model/ + MLflow run |

---

## 01 — Bronze Ingestion (Colab)

**Purpose:** Pull raw NBA data from the NBA Stats API and land it in S3 as-is.

**Dependencies:**
```bash
pip install nba_api boto3
```

**What it does:**
- Calls `LeagueGameFinder` to pull all 2024-25 game logs
- Calls `TeamEstimatedMetrics` to pull team-level stats
- Uploads both as JSON to S3 under `bronze/games/` and `bronze/team_stats/`
- Uses a timestamped run folder so each ingestion is preserved

**S3 output:**
```
bronze/games/season=2024-25/run=TIMESTAMP/games.json
bronze/team_stats/season=2024-25/run=TIMESTAMP/team_stats.json
```

---

## 02 — Silver Layer (Databricks)

**Purpose:** Read the raw bronze JSON, clean and type-cast all fields, and write Parquet back to S3.

**Dependencies:**
```bash
%pip install boto3
```
PySpark is available natively on Databricks.

**What it does:**
- Reads the latest bronze JSON file from S3 via boto3
- Creates a PySpark DataFrame from the raw row/header structure returned by nba_api
- Selects and casts relevant columns (PTS, REB, AST, TOV, PLUS_MINUS, FG_PCT, etc.)
- Drops rows with null GAME_ID, TEAM_ID, or WL
- Parses GAME_DATE strings into proper date types
- Writes cleaned Parquet files to S3 silver layer

**S3 output:**
```
silver/games/season=2024-25/*.parquet
```

---

## 03 — Gold Layer (Databricks)

**Purpose:** Apply feature engineering to the silver data to produce a model-ready dataset.

**Dependencies:**
```bash
%pip install boto3
```

**What it does:**
- Reads silver Parquet files from S3
- Derives HOME flag from MATCHUP string (contains "vs." = home)
- Derives WIN label from WL column
- Computes REST_DAYS using a window lag on GAME_DATE per team
- Computes rolling 10-game averages (AVG_PTS_L10, AVG_REB_L10, AVG_AST_L10, AVG_TOV_L10, AVG_PLUS_MINUS_L10) using PySpark window functions
- Drops rows with nulls (first ~10 games per team have no rolling average)
- Writes final feature table as Parquet to S3 gold layer

**S3 output:**
```
gold/games/season=2024-25/*.parquet
```

---

## 04 — ML Training (Databricks)

**Purpose:** Train an XGBoost classifier on the gold layer, log everything to MLflow, and save the model to S3.

**Dependencies:**
```bash
%pip install xgboost scikit-learn pyarrow boto3
```
MLflow is available natively on Databricks.

**What it does:**
- Downloads gold Parquet files from S3 into a pandas DataFrame
- Selects 7 features: HOME, REST_DAYS, AVG_PTS_L10, AVG_REB_L10, AVG_AST_L10, AVG_TOV_L10, AVG_PLUS_MINUS_L10
- Splits 80/20 train/test with random_state=42
- Trains XGBClassifier (n_estimators=100, max_depth=4, learning_rate=0.1)
- Logs parameters, accuracy, AUC-ROC, and the model artifact to MLflow
- Serializes the model as a pickle file and uploads to S3

**MLflow results:**
| Metric | Value |
|--------|-------|
| Accuracy | 58.5% |
| AUC-ROC | 0.633 |

**S3 output:**
```
model/nba_model.pkl
```

---

## Setup

Before running any notebook set your AWS credentials:

```python
import os
os.environ["AWS_ACCESS_KEY_ID"] = "your_key"
os.environ["AWS_SECRET_ACCESS_KEY"] = "your_secret"
os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
```

For Databricks notebooks, add these at the top of each notebook's Cell 2. For Colab, same pattern applies.
