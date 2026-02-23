from sqlalchemy import Column, Integer, String, DateTime
from db import Base

class Survey(Base):
    __tablename__ = "survey"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    department = Column(String, nullable=False)
    age = Column(Integer, nullable=False)
    future = Column(String, nullable=False)
    emotion = Column(String, nullable=False)
    time = Column(DateTime, nullable=False)