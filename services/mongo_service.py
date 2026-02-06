"""
MongoDB operations executor service
"""
import json
from bson import json_util

from models.schemas import MongoOperation, ActionEnum
from database.mongodb import get_collection


# ──────────────────────────── Utilities ─────────────────────────


def bson_to_json(doc):
    """BSON → JSON-serializable."""
    return json.loads(json_util.dumps(doc))


# ──────────────────────────── MongoDB Executor ──────────────────


async def execute_operation(op: MongoOperation) -> list | dict | None:
    """
    Execute MongoDB operation based on the LLM-generated operation schema
    """
    col = get_collection()
    filt = op.filter or {}

    match op.action:
        case ActionEnum.find:
            docs = await col.find(filt).to_list(length=100)
            return bson_to_json(docs)

        case ActionEnum.find_one:
            doc = await col.find_one(filt)
            return bson_to_json(doc) if doc else None

        case ActionEnum.insert_one:
            r = await col.insert_one(op.data)
            return {"inserted_id": str(r.inserted_id)}

        case ActionEnum.insert_many:
            r = await col.insert_many(op.data)
            return {"inserted_ids": [str(i) for i in r.inserted_ids]}

        case ActionEnum.update_one:
            r = await col.update_one(filt, op.update)
            return {"matched": r.matched_count, "modified": r.modified_count}

        case ActionEnum.update_many:
            r = await col.update_many(filt, op.update)
            return {"matched": r.matched_count, "modified": r.modified_count}

        case ActionEnum.delete_one:
            r = await col.delete_one(filt)
            return {"deleted": r.deleted_count}

        case ActionEnum.delete_many:
            r = await col.delete_many(filt)
            return {"deleted": r.deleted_count}

        case ActionEnum.aggregate:
            docs = await col.aggregate(op.pipeline or []).to_list(length=100)
            return bson_to_json(docs)

        case ActionEnum.count:
            return {"count": await col.count_documents(filt)}

        case _:
            return None
