import json
import re

from firebase_functions import https_fn
from google.cloud.firestore_v1 import Client


def get(db: Client) -> https_fn.Response:
    docs = db.collection("trafficStats").stream()

    result = [{**doc.to_dict(), "id": doc.id} for doc in docs]

    return https_fn.Response(json.dumps(result), content_type="application/json")

def post(req: https_fn.Request, db: Client) -> https_fn.Response:
    traffic_stat = req.get_json()
    if not is_valid_traffic_stat(traffic_stat):
        return https_fn.Response(status=422)

    existing = db.collection("trafficStats").where("date", "==", traffic_stat["date"]).limit(1).get()
    if len(existing) > 0:
        return https_fn.Response(status=409)

    doc = db.collection("trafficStats").add({"date": traffic_stat["date"], "visits": traffic_stat["visits"]})
    return https_fn.Response(json.dumps({"id": doc[1].id}), status=201, content_type="application/json")

def put(req: https_fn.Request, db: Client) -> https_fn.Response:
    doc_id = req.args.get("id")
    if not doc_id:
        return https_fn.Response(status=400)

    traffic_stat = req.get_json()
    if not is_valid_traffic_stat(traffic_stat):
        return https_fn.Response(status=422)

    doc_ref = db.collection("trafficStats").document(doc_id)
    if not doc_ref.get().exists:
        return https_fn.Response(status=404)

    existing = db.collection("trafficStats").where("date", "==", traffic_stat["date"]).limit(1).get()
    if len(existing) > 0 and existing[0].id != doc_id:
        return https_fn.Response(status=409)

    doc_ref.set({"date": traffic_stat["date"], "visits": traffic_stat["visits"]})
    return https_fn.Response(status=200)


def delete(req: https_fn.Request, db: Client) -> https_fn.Response:
    doc_id = req.args.get("id")
    if not doc_id:
        return https_fn.Response(status=400)

    doc_ref = db.collection("trafficStats").document(doc_id)
    if not doc_ref.get().exists:
        return https_fn.Response(status=404)

    doc_ref.delete()
    return https_fn.Response(status=200)

def is_valid_traffic_stat(traffic_stat: dict) -> bool:
    if not isinstance(traffic_stat.get("date"), str) or not isinstance(traffic_stat.get("visits"), int):
        return False
    if not re.match("^\d{4}-\d{2}-\d{2}$", traffic_stat.get("date")):
        return False
    if not traffic_stat.get("visits") >= 0:
        return False
    return True