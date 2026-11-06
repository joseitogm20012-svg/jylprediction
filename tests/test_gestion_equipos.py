import pytest
import mongomock


def test_coleccion_se_llama_equipos(monkeypatch):
    import database
    monkeypatch.setenv("MONGODB_URI", "mongodb://localhost:27017")
    monkeypatch.setenv("MONGODB_DB", "test_db")
    database._client = None
    col = database.get_equipos_collection(client=mongomock.MongoClient())
    assert col.name == "equipos"


def test_sin_uri_lanza_error_claro(monkeypatch):
    import database
    monkeypatch.delenv("MONGODB_URI", raising=False)
    database._client = None
    with pytest.raises(database.MongoNoConfiguradoError):
        database.get_equipos_collection()


def test_ensure_indexes_crea_indice_unico():
    import database
    col = mongomock.MongoClient().db.equipos
    database.ensure_indexes(col)
    nombres = list(col.index_information())
    assert "nombre_normalizado_1" in nombres
