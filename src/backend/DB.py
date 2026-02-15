from src.backend.ConnectionPool import Pool
from src.backend.Consts import LIMIT, PREMIUM_LIMIT
from datetime import datetime


class DB:
    def __init__(self, pool: Pool):
        self.pool = pool

    def execute(self, cmd: str, params: tuple = None):  # NEVER use when handling user input (not injection-safe)
        with self.pool.get() as conn: # FIX: cursor does not have context manager
            if params:
                cursor = conn.execute(cmd, params)
            else:
                cursor = conn.execute(cmd)
            conn.commit()
            return cursor.fetchall()

    def create_user(self, uid):
        self.execute(f"insert into Users(id) values ({uid})") # FIX: braces

    def get_user(self, uid) -> User | None: # ADD: return type
        rows = self.execute(f"select * from Users where Id=({uid})") # FIX(1,2)
        # 1: execute returns fetchall() already, return type is list
        # 2: braces
        if not rows:
            return None
        data = rows[0]
        return User(self, *data)


class User:
    def __init__(self, db, uid, balance=0, paid_requests=0, is_premium=False, premium_datetime=0, is_admin=False, last_model=None):
        self.db = db
        self.id = uid
        self.balance = balance
        self.paid_requests = paid_requests  # add to those when user buys additional requests
        self.is_premium = is_premium
        self.premium_datetime = premium_datetime   # check expiration when starting the dialogue
        self.is_admin = is_admin
        self.last_model = last_model
        self.requests = PREMIUM_LIMIT if is_premium else LIMIT

    def can_make_request(self) -> bool:
        if self.requests <= 0:
            return False
        self.requests -= 1
        return True

    def set_premium(self, value: bool):
        self.is_premium = value
        self.requests = PREMIUM_LIMIT if value else LIMIT
        self.premium_datetime = datetime.now() if value else None

    def save(self):
        if isinstance(self.db, str) and self.db == "mock":
            return
        cmd = """
            INSERT OR REPLACE INTO Users(
                id, balance, paidrequests, ispremium, premiumdate, isadmin, lastmodel
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """
        params = (
            self.id,
            self.balance,
            self.paid_requests,
            self.is_premium,
            self.premium_datetime,
            self.is_admin,
            self.last_model
        )
        self.db.execute(cmd, params)

    def reset_requests(self):
        pass

    def create_reset_timer(self):
        pass
