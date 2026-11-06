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


def test_modelo_rechaza_nombre_solo_espacios():
    from models.equipo import Equipo
    with pytest.raises(pydantic.ValidationError):
        Equipo(**_datos_validos(nombre="   "))


def test_modelo_rechaza_nombre_de_un_caracter_tras_recortar():
    from models.equipo import Equipo
    with pytest.raises(pydantic.ValidationError):
        Equipo(**_datos_validos(nombre="  A  "))


def test_modelo_acepta_nombre_de_60_caracteres_tras_recortar():
    from models.equipo import Equipo
    eq = Equipo(**_datos_validos(nombre="  " + "A" * 60 + "  "))
    assert eq.nombre == "A" * 60


def test_modelo_acepta_notas_de_500_caracteres_tras_recortar():
    from models.equipo import Equipo
    eq = Equipo(**_datos_validos(notas="  " + "x" * 500 + "  "))
    assert eq.notas == "x" * 500


def _repo():
    from controllers.equipo_controller import EquipoRepository
    col = mongomock.MongoClient().db.equipos
    import database
    database.ensure_indexes(col)
    return EquipoRepository(col)


def test_crear_y_listar_equipo():
    from controllers.equipo_controller import crear_equipo
    repo = _repo()
    res = crear_equipo(repo, _datos_validos())
    assert res.ok is True
    assert len(repo.listar()) == 1
    assert repo.listar()[0]["nombre"] == "Argentina"


def test_crear_duplicado_normalizado_falla():
    from controllers.equipo_controller import crear_equipo
    repo = _repo()
    crear_equipo(repo, _datos_validos())
    res = crear_equipo(repo, _datos_validos(nombre="  ARGENTINA "))
    assert res.ok is False
    assert "ya existe" in res.mensaje.lower()
    assert len(repo.listar()) == 1


def test_crear_con_datos_invalidos_devuelve_errores():
    from controllers.equipo_controller import crear_equipo
    repo = _repo()
    res = crear_equipo(repo, _datos_validos(ranking_fifa=300))
    assert res.ok is False
    assert res.errores
    assert repo.listar() == []


def test_actualizar_equipo():
    from controllers.equipo_controller import crear_equipo, actualizar_equipo
    repo = _repo()
    crear_equipo(repo, _datos_validos())
    eq = repo.listar()[0]
    res = actualizar_equipo(repo, eq["id"], _datos_validos(nombre="Argentina B", rating_elo=1900))
    assert res.ok is True
    assert repo.obtener(eq["id"])["nombre"] == "Argentina B"


def test_actualizar_id_invalido_devuelve_falso():
    from controllers.equipo_controller import actualizar_equipo
    repo = _repo()
    res = actualizar_equipo(repo, "no-es-objectid", _datos_validos())
    assert res.ok is False


def test_eliminar_equipo():
    from controllers.equipo_controller import crear_equipo, eliminar_equipo
    repo = _repo()
    crear_equipo(repo, _datos_validos())
    eq = repo.listar()[0]
    assert eliminar_equipo(repo, eq["id"]).ok is True
    assert repo.listar() == []
    assert eliminar_equipo(repo, eq["id"]).ok is False


from fastapi import FastAPI
from fastapi.testclient import TestClient


def _app_de_prueba():
    from routes.equipo_routes import router, get_repo
    app = FastAPI()
    app.include_router(router)
    repo = _repo()
    app.dependency_overrides[get_repo] = lambda: repo
    return app, repo


def test_lista_responde_200_y_muestra_titulo():
    app, _ = _app_de_prueba()
    r = TestClient(app).get("/gestion/equipos/")
    assert r.status_code == 200
    assert "Equipos" in r.text


def test_crear_desde_formulario_redirige_y_persiste():
    app, repo = _app_de_prueba()
    c = TestClient(app)
    r = c.post("/gestion/equipos/", data=_datos_validos(), follow_redirects=False)
    assert r.status_code == 303
    assert len(repo.listar()) == 1


def test_formulario_invalido_no_guarda_y_muestra_error():
    app, repo = _app_de_prueba()
    c = TestClient(app)
    datos = _datos_validos()
    datos["ranking_fifa"] = "300"
    r = c.post("/gestion/equipos/", data=datos)
    assert r.status_code == 400
    assert "ranking" in r.text.lower()
    assert repo.listar() == []


def test_detalle_id_invalido_da_404():
    app, _ = _app_de_prueba()
    r = TestClient(app).get("/gestion/equipos/no-es-objectid")
    assert r.status_code == 404


def test_eliminar_desde_formulario():
    app, repo = _app_de_prueba()
    from controllers.equipo_controller import crear_equipo
    crear_equipo(repo, _datos_validos())
    eq = repo.listar()[0]
    r = TestClient(app).post(f"/gestion/equipos/{eq['id']}/eliminar", follow_redirects=False)
    assert r.status_code == 303
    assert repo.listar() == []


def test_mongo_sin_configurar_da_503(monkeypatch):
    import database
    from routes.equipo_routes import router, get_repo
    app = FastAPI()
    app.include_router(router)
    monkeypatch.delenv("MONGODB_URI", raising=False)
    database._client = None
    app.dependency_overrides.pop(get_repo, None)
    r = TestClient(app).get("/gestion/equipos/")
    assert r.status_code == 503
    assert "MongoDB" in r.text
