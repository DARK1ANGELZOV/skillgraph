def test_register_owner_and_me(client):
    response = client.post(
        "/api/auth/register-owner",
        json={
            "email": "owner@company.dev",
            "password": "secret123",
            "company_name": "Acme",
            "full_name": "Owner One",
        },
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["role"] == "OWNER"

    me = client.get("/api/auth/me")
    assert me.status_code == 200
    assert me.json()["email"] == "owner@company.dev"


def test_login_after_register(client):
    client.post(
        "/api/auth/register-owner",
        json={
            "email": "owner2@company.dev",
            "password": "secret123",
            "company_name": "Acme Two",
            "full_name": "Owner Two",
        },
    )
    client.post("/api/auth/logout")

    response = client.post(
        "/api/auth/login",
        json={"email": "owner2@company.dev", "password": "secret123"},
    )
    assert response.status_code == 200
    assert response.json()["role"] == "OWNER"
