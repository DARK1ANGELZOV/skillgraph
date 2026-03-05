from app.core.security import get_password_hash, verify_password


def test_password_hash_roundtrip():
    password = "strong-password"
    hashed = get_password_hash(password)
    assert hashed != password
    assert verify_password(password, hashed)
