from sqlite3.dbapi2 import connect
from flask import g
import sqlite3
import psycopg2
from psycopg2.extras import DictCursor



def connect_db():
    conn = psycopg2.connect("postgres://hqcoiixtrnwijc:553e6cf0c033013734524ba70510d5b1259f9a50d1244c9fdc730eb136dc8b01@ec2-18-233-83-165.compute-1.amazonaws.com:5432/d3qe2970kr37av",cursor_factory=DictCursor)
    conn.autocommit = True
    sql = conn.cursor()
    return conn,sql

def get_db():
    db = connect_db()
    
    if not hasattr(g,"postgres_db_conn"):
        g.postgres_db_conn = db[0]

    if not hasattr(g,"postgres_db_cur"):
        g.postgres_db_cur = db[1]

    return g.postgres_db_cur

def init_db():
    db = connect_db()

    db[1].execute(open("schema.sql","r").read())
    db[1].close()

    db[0].close()

def init_admin():
    db = connect_db()
    db[1].execute("UPDATE users SET admin = True WHERE name = %s ",("admin",))

    db[1].close()
    db[0].close()

