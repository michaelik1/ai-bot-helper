import sqlite3
from queue import Queue
from Consts import DB_PATH


class Pool:
    def __init__(self, number_of_connections: int):
        self.num = number_of_connections
        self.pool = Queue(-1)
        for i in range(self.num):
            self.pool.put(sqlite3.connect(DB_PATH))

    def get(self):
        while True:
            conn = self.pool.get()
            if Pool.check_alive(conn):
                return PooledConnection(self, conn)
            self.pool.put(sqlite3.connect(DB_PATH))

    def release(self, conn: sqlite3.Connection):
        self.pool.put(sqlite3.connect(DB_PATH))

    @staticmethod
    def check_alive(conn: sqlite3.Connection):
        try:
            conn.execute("select 1")
            return True
        except Exception:
            return False


class PooledConnection:
    def __init__(self, pool: Pool, conn: sqlite3.Connection):
        self.pool = pool
        self.conn = conn

    def __enter__(self):
        return self.conn

    def __exit__(self, exc_type, exc, tb):
        if exc_type:
            self.conn.rollback()
        else:
            self.conn.commit()

        self.pool.release(self.conn)
