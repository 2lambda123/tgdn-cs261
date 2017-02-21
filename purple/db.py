# -*- coding: utf-8 -*-

import sys
import rethinkdb as r
from rethinkdb.errors import RqlRuntimeError, RqlDriverError

from contextlib import contextmanager
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    BigInteger,
    Float,
    String,
    Boolean,
    ForeignKey
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.engine.url import URL
from sqlalchemy.orm import sessionmaker, relationship

RDB_HOST = 'localhost'
RDB_PORT = '28015'
PURPLE_DB = 'purple'

DATABASE_SETTINGS = {
    'drivername': 'postgres',
    'host': 'localhost',
    'port': '5432',
    'username': 'purple',
    'password': 'purple123',
    'database': 'cs261'
}

# create database engine and setup session
engine = create_engine(URL(**DATABASE_SETTINGS))
Base = declarative_base(bind=engine)
Session = sessionmaker(bind=engine)
session = Session()


@contextmanager
def get_reql_connection(db=False):
    """
    Make rdb connection available as context manager generator.
    ie:
    with get_reql_connection(db=True) as conn:
        r.table('sometable').run(conn)
    """
    try:
        if db:
            rdb_conn = r.connect(host=RDB_HOST, port=RDB_PORT, db=PURPLE_DB)
        else:
            rdb_conn = r.connect(host=RDB_HOST, port=RDB_PORT)
    except RqlDriverError:
        sys.stderr.write('Rethinkdb: No db connection could be established.')
        sys.exit(1)

    try:
        yield rdb_conn
    finally:
        rdb_conn.close()


#####################################
#           Public Methods          #
#####################################

def create_tables():
    '''
    Create all tables
    '''
    # Postgres
    Base.metadata.create_all(engine)

    # Rethinkdb
    with get_reql_connection() as conn:
        try:
            r.db_create(PURPLE_DB).run(conn)
            # r.db(PURPLE_DB).table_create('trades').run(conn)
            r.db(PURPLE_DB).table_create('alerts').run(conn)
            ## TODO: create alert table (think of design)
        except RqlRuntimeError:
            # fail silently
            # Remember to reset db first to migrate db
            pass
        finally:
            print 'Rethinkdb setup complete.'


def drop_tables():
    '''
    Delete all data in the tables (destroy databases)
    '''
    # Postgres
    Base.metadata.drop_all(engine)

    # Rethinkdb
    with get_reql_connection() as conn:
        try:
            r.db_drop(PURPLE_DB).run(conn)
        except RqlRuntimeError:
            pass


######################################
#               Models               #
######################################

class BaseModel(Base):
    __abstract__ = True
    id = Column(Integer, primary_key=True)

class SymbolModel(Base):
    __tablename__ = 'symbols'
    name = Column(String, primary_key=True)
    trades = relationship('TradeModel', back_populates='symbol')

    @classmethod
    def get_or_create(cls, name):
        # retrieve symbol or create a new one and return
        obj = session.query(cls).filter_by(name=name).one_or_none()
        if not obj:
            obj = cls(name=name)
            session.add(obj)
            session.commit()
        return obj


class TradeModel(BaseModel):
    '''
    Table that holds data from each trade.
    Add required attributes below.
    '''
    __tablename__ = 'trades'

    price = Column(Float)
    size = Column(BigInteger)
    flagged = Column(Boolean, default=False)
    symbol_name = Column(String, ForeignKey('symbols.name'))

    symbol = relationship('SymbolModel', back_populates='trades')

    def flag(self, truth_value):
        self.flagged = truth_value
        session.commit()