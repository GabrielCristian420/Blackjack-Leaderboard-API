from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from settings import get_settings

settings = get_settings()

# Pentru SQLite trebuie check_same_thread=False; pentru Postgres nu este necesar.
connect_args = (
    {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
)

# engine-ul este cel care comunică cu baza de date
engine = create_engine(
    settings.database_url,
    connect_args=connect_args,
)

# Sesiunea ne va permite să facem interogări (queries)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Clasa de bază din care vor moșteni modelele noastre
Base = declarative_base()
