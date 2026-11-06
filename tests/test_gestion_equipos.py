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


import pydantic


def _datos_validos(**overrides):
    base = {
        "nombre": "Argentina",
        "confederacion": "CONMEBOL",
        "ranking_fifa": 1,
        "rating_elo": 2050.5,
    }
    base.update(overrides)
    return base


def test_modelo_acepta_datos_validos():
    from models.equipo import Equipo
    eq = Equipo(**_datos_validos())
    assert eq.nombre == "Argentina"


def test_modelo_recorta_espacios_del_nombre():
    from models.equipo import Equipo
    eq = Equipo(**_datos_validos(nombre="  Argentina  "))
    assert eq.nombre == "Argentina"


@pytest.mark.parametrize("campo,valor", [
    ("nombre", "A"),
    ("confederacion", "MARTE"),
    ("ranking_fifa", 0),
    ("ranking_fifa", 212),
    ("rating_elo", 999),
])
def test_modelo_rechaza_valores_invalidos(campo, valor):
    from models.equipo import Equipo
    with pytest.raises(pydantic.ValidationError):
        Equipo(**_datos_validos(**{campo: valor}))


def test_modelo_rechaza_escudo_que_no_es_url():
    from models.equipo import Equipo
    with pytest.raises(pydantic.ValidationError):
        Equipo(**_datos_validos(escudo_url="no-es-una-url"))


def test_modelo_rechaza_escudo_demasiado_largo():
    from models.equipo import Equipo
    with pytest.raises(pydantic.ValidationError):
        Equipo(**_datos_validos(escudo_url="https://" + "a" * 300 + ".com/x.png"))
