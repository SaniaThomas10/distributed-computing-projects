import json
import os
import time
import logging
from datetime import datetime, timezone
from decimal import Decimal

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

sqs = boto3.client("sqs")
dynamodb = boto3.resource("dynamodb")

RESULTS_QUEUE_URL = os.environ.get("RESULTS_QUEUE_URL", "")
DYNAMO_TABLE_NAME = os.environ.get("DYNAMO_TABLE_NAME", "")

RELEVANCE_MAP = {
("sports", "sportswear"): 1.4,
("sports", "energy_drink"): 1.3,
("finance", "fintech"): 1.5,
("finance", "insurance"): 1.3,
("entertainment", "streaming"): 1.4,
("entertainment", "gaming"): 1.3,
("lifestyle", "beauty"): 1.3,
("lifestyle", "travel"): 1.2,
}

TIME_WINDOWS = [
(6, 9, 1.20),
(12, 14, 1.15),
(19, 23, 1.25),
]

DEVICE_BONUS = {
"mobile": 1.1,
"desktop": 1.0,
}

# -------------------------------

# Task 1

# -------------------------------

def compute_score(bid, opportunity):
    bid_amount = bid.get("bid_amount", 0)
    if not bid_amount:
        return 0.0

    relevance = RELEVANCE_MAP.get(
        (opportunity["content_category"], bid["category"]),
        1.0
    )

    try:
        hour = int(opportunity["timestamp"][11:13])
    except:
        hour = 0

    time_bonus = 1.0
    for start, end, bonus in TIME_WINDOWS:
        if start <= hour < end:
            time_bonus = bonus
            break

    device_bonus = DEVICE_BONUS.get(opportunity["device_type"], 1.0)

    return bid_amount * relevance * time_bonus * device_bonus

# -------------------------------

# Task 2

# -------------------------------

def select_winner(opportunity):
    bids = opportunity.get("bids", [])
    if not bids:
        return None

    scored = []

    for bid in bids:
        score = compute_score(bid, opportunity)
        scored.append({
            "advertiser_id": bid["advertiser_id"],
            "bid_amount": bid["bid_amount"],
            "score": score
        })

    scored.sort(key=lambda x: x["score"], reverse=True)

    winner = scored[0]
    second_score = scored[1]["score"] if len(scored) > 1 else 0

    return {
        "winning_advertiser_id": winner["advertiser_id"],
        "winning_bid_amount": winner["bid_amount"],
        "winning_score": winner["score"],
        "score_margin": winner["score"] - second_score,
    }

# -------------------------------

# Task 3

# -------------------------------

def process_opportunity(opportunity):
    result = select_winner(opportunity)

    if result is None:
        return None

    processed_at = datetime.now(timezone.utc).isoformat()

    return {
        "opportunity_id": opportunity["opportunity_id"],
        "content_category": opportunity["content_category"],
        "winning_advertiser_id": result["winning_advertiser_id"],
        "winning_bid_amount": result["winning_bid_amount"],
        "winning_score": result["winning_score"],
        "score_margin": result["score_margin"],
        "processed_at": processed_at,
    }

# -------------------------------

# Task 4

# -------------------------------

def lambda_handler(event, context):
    start = time.perf_counter()

    table = dynamodb.Table(DYNAMO_TABLE_NAME)
    failures = []

    for record in event["Records"]:
        try:
            body = json.loads(record["body"])

            result = process_opportunity(body)

            if result is None:
                continue

            # Convert floats for DynamoDB
            ddb_item = {
                k: Decimal(str(v)) if isinstance(v, float) else v
                for k, v in result.items()
            }

            table.put_item(Item=ddb_item)

            sqs.send_message(
                QueueUrl=RESULTS_QUEUE_URL,
                MessageBody=json.dumps(result)
            )

        except Exception as e:
            logger.error("Failed processing message %s: %s", record["messageId"], str(e))
            failures.append({
                "itemIdentifier": record["messageId"]
            })

    elapsed_ms = (time.perf_counter() - start) * 1000
    logger.info("Batch complete in %.1f ms", elapsed_ms)

    return {"batchItemFailures": failures}
