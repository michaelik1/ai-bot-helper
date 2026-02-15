from collections import defaultdict
from asyncio import Lock, to_thread, sleep as async_sleep
from src.backend.DB import DB, User
from src.backend.ConnectionPool import Pool

class UserManager:
    _users: dict[int, User] = {}
    _db: DB | None = None
    _is_mock = False
    _mock_delay_ms: int | None = None
    _user_locks: dict[int, Lock] = defaultdict(Lock)

    @classmethod
    def setup(cls, mock: bool = False, mock_delay_ms: int = 0):
        cls._is_mock = mock
        cls._mock_delay_ms = mock_delay_ms
        cls._users = {}
        if mock:
            cls._db = None
            return

        db_pool = Pool(number_of_connections=1)
        cls._db = DB(pool=db_pool)

    @classmethod
    async def get_user(cls, user_id: int) -> User:
        if cls._is_mock:
            if cls._mock_delay_ms:
                await async_sleep(cls._mock_delay_ms / 1000)
            cached = cls._users.get(user_id)
            if cached is not None:
                return cached
            user = User("mock", user_id, last_model="LLaMA-8b")
            cls._users[user_id] = user
            return user
        if cls._db is None:
            raise RuntimeError("Run setup method first, class is uninitialized")
        cached = cls._users.get(user_id)
        if cached is not None:
            return cached
        lock = cls._user_locks[user_id]
        async with lock:
            cached = cls._users.get(user_id)
            if cached is not None:
                return cached
            user = await to_thread(cls._db.get_user, user_id)
            if user is None:
                await to_thread(cls._db.create_user, user_id)
                user = await to_thread(cls._db.get_user, user_id)
            if user is None:
                raise RuntimeError(f"Failed to create/load user_id={user_id}")
            cls._users[user_id] = user
            return user