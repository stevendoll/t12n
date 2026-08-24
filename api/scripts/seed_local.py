"""
Seed local DynamoDB with icebreaker sentences.
Run: DYNAMODB_ENDPOINT=http://localhost:8000 pipenv run python scripts/seed_local.py
"""

import os
import uuid
import boto3
from datetime import datetime, timezone

ENDPOINT = os.environ.get("DYNAMODB_ENDPOINT")  # None = use real AWS
REGION = "us-east-1"

_kwargs = {"endpoint_url": ENDPOINT} if ENDPOINT else {}
dynamodb = boto3.resource("dynamodb", region_name=REGION, **_kwargs)

ICEBREAKERS = [
    "This might be the biggest revolution of your career. It's also drinking your water supply to draft emails. [laughter] Let's talk about that.",
    "Nine companies own most of the world's AI compute. Rent power from them wisely, or hand them your strategy for free.",
    "The new job nobody warned you about: babysitting software that loses its mind at 2am. [laughter] Welcome to the future.",
    "AI didn't take your job. It's just really good at pretending it could.",
    "Somewhere, a tycoon's yacht got a little bigger this quarter. Not yours though. Let's fix that.",
    "Your board wants an AI answer. 'We're thinking carefully' is a real one — for about two more quarters.",
    "Misinformation travels faster with AI now. So does actual work. The tool doesn't pick a side. You do.",
    "Skipping AI because it's messy is like skipping electricity because Edison was kind of a jerk. [laughter] Fair instinct. Still miss the whole thing.",
    "Everyone you know is either an AI true believer or an AI doomer. Both are exhausting at dinner parties.",
    "The last AI initiative promised transformation. It delivered a confident chatbot and a slide deck nobody read.",
    "Moving fast without a plan is expensive. So is moving slow and calling it due diligence.",
    "Your competitors aren't scared of AI. They're scared of explaining to the board why they waited.",
    "AI makes mistakes. [laughter] So does your quarterly forecast. Only one of them is improving every month.",
    "The data you need to decide is already inside your company. Finding it was never the hard part.",
    "Nobody asks 'should we use electricity' anymore. Someday nobody asks this about AI either. The only real question is whether you paid attention on the way there.",
]


def create_tables():
    existing = [t.name for t in dynamodb.tables.all()]

    if "icebreakers" not in existing:
        dynamodb.create_table(
            TableName="icebreakers",
            AttributeDefinitions=[
                {"AttributeName": "icebreaker_id", "AttributeType": "S"},
                {"AttributeName": "is_active", "AttributeType": "S"},
            ],
            KeySchema=[{"AttributeName": "icebreaker_id", "KeyType": "HASH"}],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "is_active-index",
                    "KeySchema": [{"AttributeName": "is_active", "KeyType": "HASH"}],
                    "Projection": {"ProjectionType": "ALL"},
                }
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        print("Created table: icebreakers")
    else:
        print("Table already exists: icebreakers")

    if "conversation_turns" not in existing:
        dynamodb.create_table(
            TableName="conversation_turns",
            AttributeDefinitions=[
                {"AttributeName": "conversation_id", "AttributeType": "S"},
                {"AttributeName": "order", "AttributeType": "N"},
            ],
            KeySchema=[
                {"AttributeName": "conversation_id", "KeyType": "HASH"},
                {"AttributeName": "order", "KeyType": "RANGE"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        print("Created table: conversation_turns")
    else:
        print("Table already exists: conversation_turns")


def seed_icebreakers():
    table = dynamodb.Table("icebreakers")
    now = datetime.now(timezone.utc).isoformat()
    count = 0
    for text in ICEBREAKERS:
        table.put_item(Item={
            "icebreaker_id": str(uuid.uuid4()),
            "text": text,
            "is_active": "true",
            "created_at": now,
        })
        count += 1
    print(f"Seeded {count} icebreakers")


if __name__ == "__main__":
    create_tables()
    seed_icebreakers()
    print("Done.")
