from app.core.security import hash_password, verify_password


def test_hash_password_does_not_store_plaintext():
    password = "TestPassword123"

    password_hash = hash_password(password)

    assert password_hash != password
    assert password_hash.startswith("$argon2id$")


def test_hash_password_generates_different_hashes():
    password = "TestPassword123"

    first_hash = hash_password(password)
    second_hash = hash_password(password)

    assert first_hash != second_hash


def test_verify_password_accepts_correct_password():
    password = "TestPassword123"
    password_hash = hash_password(password)

    assert verify_password(password, password_hash) is True


def test_verify_password_rejects_wrong_password():
    password_hash = hash_password("TestPassword123")

    assert verify_password("WrongPassword", password_hash) is False
