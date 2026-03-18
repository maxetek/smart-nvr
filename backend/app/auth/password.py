import argon2
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

# Argon2id with OWASP 2024 recommended parameters
_hasher = PasswordHasher(
    time_cost=2,
    memory_cost=19456,  # 19 MiB
    parallelism=1,
    hash_len=32,
    salt_len=16,
    type=argon2.Type.ID,
)


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, hash: str) -> bool:
    try:
        return _hasher.verify(hash, password)
    except VerifyMismatchError:
        return False


def needs_rehash(hash: str) -> bool:
    return _hasher.check_needs_rehash(hash)
