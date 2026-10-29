from sqlalchemy import Boolean, Column, Integer, String, JSON, DateTime
from database import Base
from datetime import datetime

class Analysis(Base):
    __tablename__ ="analysis"

    id = Column(Integer, primary_key=True, index = True)
    filename = Column(String, nullable = False)
    user_prompt = Column(String, nullable = False)
    route = Column(String, nullable = False)
    company_name = Column(String, nullable = True)
    fiscal_period = Column(String, nullable=True)
    metrics       = Column(JSON, nullable=True)
    analysis      = Column(JSON, nullable=True)
    risks         = Column(JSON, nullable=True)
    report        = Column(JSON, nullable=True)
    created_at    = Column(DateTime, default=datetime.utcnow)
    latency_seconds = Column(Integer, nullable=True)
    
class APIKey(Base):
    __tablename__ ="api_keys"
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, nullable=False, index=True)
    owner_name = Column(String, nullable=False)
    is_active  = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)