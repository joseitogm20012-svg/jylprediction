from dataclasses import dataclass, field
from typing import Any

from bson import ObjectId
from pymongo.collection import Collection
from pymongo.errors import DuplicateKeyError
from pydantic import ValidationError

from models.equipo import Equipo

CAMPOS_EQUIPO = (
    "nombre",
    "confederacion",
    "ranking_fifa",
    "rating_elo",
    "escudo_url",
    "notas",
)

CAMPOS_OPCIONALES_VACIOS = ("escudo_url", "notas")


@dataclass
class Resultado:
    ok: bool
    mensaje: str
    errores: list[str] = field(default_factory=list)


class EquipoDuplicadoError(Exception):
    """Se lanza cuando ya existe un equipo con el mismo nombre normalizado."""


class EquipoNoEncontradoError(Exception):
    """Se lanza cuando el equipo solicitado no existe."""


def _normalizar_nombre(nombre: str) -> str:
    return nombre.strip().lower()


class EquipoRepository:
    def __init__(self, collection: Collection):
        self.collection = collection

    def listar(self) -> list[dict]:
        return [self._documento_a_dict(doc) for doc in self.collection.find().sort("nombre", 1)]

    def obtener(self, equipo_id: str) -> dict | None:
        if not ObjectId.is_valid(equipo_id):
            return None
        doc = self.collection.find_one({"_id": ObjectId(equipo_id)})
        if doc is None:
            return None
        return self._documento_a_dict(doc)

    def crear(self, datos: dict) -> str:
        documento = self._preparar_documento(datos)
        try:
            resultado = self.collection.insert_one(documento)
        except DuplicateKeyError as exc:
            raise EquipoDuplicadoError("Ya existe un equipo con ese nombre") from exc
        return str(resultado.inserted_id)

    def actualizar(self, equipo_id: str, datos: dict) -> bool:
        if not ObjectId.is_valid(equipo_id):
            return False
        documento = self._preparar_documento(datos)
        try:
            resultado = self.collection.update_one(
                {"_id": ObjectId(equipo_id)}, {"$set": documento}
            )
        except DuplicateKeyError as exc:
            raise EquipoDuplicadoError("Ya existe un equipo con ese nombre") from exc
        return resultado.matched_count == 1

    def eliminar(self, equipo_id: str) -> bool:
        if not ObjectId.is_valid(equipo_id):
            return False
        resultado = self.collection.delete_one({"_id": ObjectId(equipo_id)})
        return resultado.deleted_count == 1

    @staticmethod
    def _preparar_documento(datos: dict) -> dict:
        documento = {campo: datos[campo] for campo in CAMPOS_EQUIPO if campo in datos}
        documento["nombre_normalizado"] = _normalizar_nombre(documento.get("nombre", ""))
        return documento

    @staticmethod
    def _documento_a_dict(doc: dict) -> dict:
        limpio = dict(doc)
        limpio["id"] = str(limpio.pop("_id"))
        limpio.pop("nombre_normalizado", None)
        return limpio


def _normalizar_formulario(datos: dict) -> dict:
    limpio = dict(datos)
    for campo in CAMPOS_OPCIONALES_VACIOS:
        valor = limpio.get(campo)
        if isinstance(valor, str) and not valor.strip():
            limpio[campo] = None
    return limpio


def _validar(datos: dict) -> tuple[dict | None, list[str]]:
    normalizados = _normalizar_formulario(datos)
    try:
        equipo = Equipo(**normalizados)
    except ValidationError as exc:
        errores = []
        for error in exc.errors():
            campo = ".".join(str(parte) for parte in error["loc"])
            errores.append(f"{campo}: {error['msg']}")
        return None, errores

    limpio: dict[str, Any] = equipo.model_dump()
    if limpio.get("escudo_url") is not None:
        limpio["escudo_url"] = str(limpio["escudo_url"])
    return limpio, []


def crear_equipo(repo: EquipoRepository, datos: dict) -> Resultado:
    limpio, errores = _validar(datos)
    if errores:
        return Resultado(False, "Revisa los datos del formulario", errores)
    try:
        repo.crear(limpio)
    except EquipoDuplicadoError:
        return Resultado(False, "Ya existe un equipo con ese nombre")
    return Resultado(True, "Equipo creado correctamente")


def actualizar_equipo(repo: EquipoRepository, equipo_id: str, datos: dict) -> Resultado:
    limpio, errores = _validar(datos)
    if errores:
        return Resultado(False, "Revisa los datos del formulario", errores)
    try:
        actualizado = repo.actualizar(equipo_id, limpio)
    except EquipoDuplicadoError:
        return Resultado(False, "Ya existe un equipo con ese nombre")
    except EquipoNoEncontradoError:
        return Resultado(False, "Equipo no encontrado")
    if not actualizado:
        return Resultado(False, "Equipo no encontrado")
    return Resultado(True, "Equipo actualizado correctamente")


def eliminar_equipo(repo: EquipoRepository, equipo_id: str) -> Resultado:
    try:
        eliminado = repo.eliminar(equipo_id)
    except EquipoNoEncontradoError:
        return Resultado(False, "Equipo no encontrado")
    if not eliminado:
        return Resultado(False, "Equipo no encontrado")
    return Resultado(True, "Equipo eliminado correctamente")
