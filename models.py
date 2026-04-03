from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, Integer, String
from database import Base


class Score(Base):
    __tablename__ = "scores"

    id = Column(Integer, primary_key=True, index=True)
    player_name = Column(String(50), index=True, nullable=False)
    score = Column(Integer, index=True, nullable=False)
    timestamp = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
