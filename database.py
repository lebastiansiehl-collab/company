from sqlalchemy import create_engine, Column, Integer, String, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Datenbank-Pfad (liegt im Ordner /data)
engine = create_engine('sqlite:///data/arbeitsmedizin.db')
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine)

class Einsatz(Base):
    __tablename__ = 'einsaetze'
    id = Column(Integer, primary_key=True)
    betrieb_id = Column(Integer)
    datum = Column(Date)
    stunden = Column(Integer)
    status = Column(String)

# Tabellen erstellen
Base.metadata.create_all(engine)
