from sqlalchemy import Column, Integer, String, Text
from models.base import Base


class Credential(Base):
    __tablename__ = "credentials"

    id = Column(Integer, primary_key=True, autoincrement=True)
    service = Column(String(64), nullable=False, unique=True, index=True)
    encrypted_key = Column(Text, nullable=False)
    created_at = Column(String(32), nullable=False)
    updated_at = Column(String(32), nullable=False)

    def __repr__(self):
        return f"<Credential {self.service}>"
