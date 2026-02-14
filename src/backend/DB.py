from ConnectionPool import Pool
from Consts import LIMIT, PREMIUM_LIMIT
from datetime import datetime


class DB:
    def __init__(self, pool: Pool):
        self.pool = pool

    def execute(self, cmd: str):  # NEVER use when handling user input (not injection-safe)
        with self.pool.get() as conn:
            with conn.execute(cmd) as cur:
                return cur.fetchall()

    def create_user(self, uid):
        self.execute(f"insert into Users(id) values {uid}")

    def get_user(self, uid):
        data = self.execute(f"select * from Users where Id={uid}").fetchone()
        return User(self, *data)


class User:
    def __init__(self, db, uid, balance=0, paid_requests=0, is_premium=False, premium_datetime=0, is_admin=False):
        self.db = db
        self.id = uid
        self.balance = balance
        self.paid_requests = paid_requests  # add to those when user buys additional requests
        self.is_premium = is_premium
        self.premium_datetime = premium_datetime   # check expiration when starting the dialogue
        self.is_admin = is_admin
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
        cmd = f"insert into Users(id, balance, paidrequests, ispremium, premiumdate, isadmin) \
        values({self.id}, {self.balance}, {self.paid_requests}, {self.is_premium}, \
        {self.premium_datetime}, {self.is_admin})"
        self.db.execute(cmd)

    def reset_requests(self):
        pass

    def create_reset_timer(self):
        pass
