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

from sqlalchemy import Column, Integer, String, DateTime, Text
from db import Base

class SurveyV2(Base):
    __tablename__ = "survey_v2"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False)
    department = Column(String, nullable=False)
    age = Column(Integer, nullable=False)

    q1_future_state = Column(String, nullable=False)
    q2_emotion_impact = Column(String, nullable=False)
    q3_obstacles = Column(Text, nullable=False)  # 多選用逗號存
    q4_solution = Column(String, nullable=False)
    q5_help_channel = Column(String, nullable=False)
    q6_avoid = Column(String, nullable=False)
    q7_prefer = Column(String, nullable=False)

    time = Column(DateTime, nullable=False)