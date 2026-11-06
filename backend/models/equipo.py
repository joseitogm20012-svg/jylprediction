from typing import Literal

from pydantic import BaseModel, Field, HttpUrl, field_validator

CONFEDERACIONES = ("CONCACAF", "CONMEBOL", "UEFA", "CAF", "AFC", "OFC")


class Equipo(BaseModel):
    nombre: str
    confederacion: Literal["CONCACAF", "CONMEBOL", "UEFA", "CAF", "AFC", "OFC"]
    ranking_fifa: int = Field(ge=1, le=211)
    rating_elo: float = Field(ge=1000, le=2200)
    escudo_url: HttpUrl | None = None
    notas: str | None = None

    @field_validator("nombre")
    @classmethod
    def _limpiar_nombre(cls, valor: str) -> str:
        limpio = valor.strip()
        if not 2 <= len(limpio) <= 60:
            raise ValueError("El nombre debe tener entre 2 y 60 caracteres")
        return limpio

    @field_validator("notas")
    @classmethod
    def _limpiar_notas(cls, valor: str | None) -> str | None:
        if valor is None:
            return None
        limpio = valor.strip()
        if len(limpio) > 500:
            raise ValueError("Las notas no pueden superar 500 caracteres")
        return limpio or None

    @field_validator("escudo_url")
    @classmethod
    def _limitar_escudo(cls, valor: HttpUrl | None) -> HttpUrl | None:
        if valor is not None and len(str(valor)) > 300:
            raise ValueError("La URL del escudo no puede superar 300 caracteres")
        return valor
