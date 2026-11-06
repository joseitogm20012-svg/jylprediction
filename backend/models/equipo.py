from typing import Literal

from pydantic import BaseModel, Field, HttpUrl, field_validator

CONFEDERACIONES = ("CONCACAF", "CONMEBOL", "UEFA", "CAF", "AFC", "OFC")


class Equipo(BaseModel):
    nombre: str = Field(min_length=2, max_length=60)
    confederacion: Literal["CONCACAF", "CONMEBOL", "UEFA", "CAF", "AFC", "OFC"]
    ranking_fifa: int = Field(ge=1, le=211)
    rating_elo: float = Field(ge=1000, le=2200)
    escudo_url: HttpUrl | None = None
    notas: str | None = Field(default=None, max_length=500)

    @field_validator("nombre")
    @classmethod
    def _limpiar_nombre(cls, valor: str) -> str:
        return valor.strip()

    @field_validator("notas")
    @classmethod
    def _limpiar_notas(cls, valor: str | None) -> str | None:
        if valor is None:
            return None
        limpio = valor.strip()
        return limpio or None

    @field_validator("escudo_url")
    @classmethod
    def _limitar_escudo(cls, valor: HttpUrl | None) -> HttpUrl | None:
        if valor is not None and len(str(valor)) > 300:
            raise ValueError("La URL del escudo no puede superar 300 caracteres")
        return valor
