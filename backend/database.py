import os
from pymongo import MongoClient, ASCENDING
from pymongo.collection import Collection


class MongoNoConfiguradoError(RuntimeError):
    """Se lanza cuando falta MONGODB_URI en el entorno."""


_client: MongoClient | None = None


def _get_client() -> MongoClient:
    global _client
    uri = os.environ.get("MONGODB_URI", "").strip()
    if not uri:
        raise MongoNoConfiguradoError(
            "MongoDB no configurado. Define MONGODB_URI en el archivo .env"
        )
    if _client is None:
        _client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    return _client


def get_equipos_collection(client: MongoClient | None = None) -> Collection:
    db_name = os.environ.get("MONGODB_DB", "jly_predictor").strip() or "jly_predictor"
    cli = client if client is not None else _get_client()
    return cli[db_name]["equipos"]


def ensure_indexes(collection: Collection) -> None:
    collection.create_index([("nombre_normalizado", ASCENDING)], unique=True)


def close_client() -> None:
    global _client
    if _client is not None:
        _client.close()
        _client = None
