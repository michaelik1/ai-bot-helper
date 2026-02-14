from src.backend.DB import DB, User
from src.backend.ConnectionPool import Pool

class UserManager:
    _users: dict[int, User] = {}
    _db: 'DB' = None

    @classmethod
    def setup(cls):
        db_pool = Pool(number_of_connections=1)
        cls._db = DB(pool=db_pool)

    @classmethod
    async def get_user(cls, user_id: int) -> User:
        if cls._db is None:
            raise Exception("Run setup method first, class is uninitialized")
        if user_id not in cls._users:
            user = cls._db.get_user(user_id)
            if user is None:
                cls._users[user_id] = cls._db.create_user(user_id)
                cls._users[user_id] = cls._db.get_user(user_id)
            else:
                cls._users[user_id] = user
        return cls._users[user_id]