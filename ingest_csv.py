import csv
import json
import urllib.request

with open(r"C:\Users\Admin\Downloads\customer_feedback.csv", newline="", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

batch = [
    {
        "source": r["customer_segment"].lower(),
        "raw_text": r["feedback"],
        "metadata_": {"feedback_id": r["feedback_id"], "segment": r["customer_segment"]},
    }
    for r in rows
]

req = urllib.request.Request(
    "http://localhost:8000/api/v1/feedback/ingest/batch",
    data=json.dumps(batch).encode(),
    headers={"Content-Type": "application/json"},
    method="POST",
)

with urllib.request.urlopen(req) as res:
    body = json.loads(res.read())
    print("Status :", body["status"])
    print("Message:", body["message"])
    print("Ingested:", len(body["data"]), "items")
    for item in body["data"][:3]:
        print(" -", item["source"], "|", item["raw_text"][:60])
    if len(body["data"]) > 3:
        print(f"  ... and {len(body['data']) - 3} more")
