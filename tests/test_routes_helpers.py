from app import create_app
from app import repositories as repo
from app import routes
from app.routes import _float_value, _safe_int
from werkzeug.security import generate_password_hash


def test_safe_int_returns_default_for_invalid_value():
    assert _safe_int("abc", 7) == 7
    assert _safe_int(None, 3) == 3


def test_float_value_accepts_comma_decimal():
    app = create_app()

    with app.test_request_context(method="POST", data={"meta": "12,5"}):
        assert _float_value("meta") == 12.5


def test_float_value_returns_none_for_invalid_value():
    app = create_app()

    with app.test_request_context(method="POST", data={"meta": "abc"}):
        assert _float_value("meta") is None


def test_login_requires_csrf_token():
    app = create_app()

    with app.test_client() as client:
        response = client.post("/login", data={"username": "admin", "password": "admin123"})

    assert response.status_code == 400


def test_login_page_uses_standalone_layout():
    app = create_app()

    with app.test_client() as client:
        response = client.get("/login")

    html = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "Ingresar" in html
    assert 'id="sidebar"' not in html


def test_login_sets_session(monkeypatch):
    app = create_app()
    routes._LOGIN_ATTEMPTS.clear()
    password_hash = generate_password_hash("admin123")

    monkeypatch.setattr(
        repo,
        "get_user_by_username",
        lambda username: {
            "id": 1,
            "username": username,
            "password_hash": password_hash,
            "nombre": "Administrador",
            "role": "ADMIN",
            "is_active": 1,
        },
    )

    with app.test_client() as client:
        with client.session_transaction() as session:
            session["_csrf_token"] = "test-token"

        response = client.post(
            "/login",
            data={"username": "admin", "password": "admin123", "_csrf_token": "test-token"},
        )

        with client.session_transaction() as session:
            user_id = session["user_id"]

    assert response.status_code == 302
    assert response.headers["Location"] == "/panel"
    assert user_id == 1


def test_change_password_updates_hash(monkeypatch):
    app = create_app()
    old_hash = generate_password_hash("admin123")
    saved = {}

    monkeypatch.setattr(
        repo,
        "get_user_by_id",
        lambda user_id: {
            "id": user_id,
            "username": "admin",
            "nombre": "Administrador",
            "role": "ADMIN",
            "is_active": 1,
        },
    )
    monkeypatch.setattr(
        repo,
        "get_user_by_username",
        lambda username: {
            "id": 1,
            "username": username,
            "password_hash": old_hash,
            "nombre": "Administrador",
            "role": "ADMIN",
            "is_active": 1,
        },
    )
    monkeypatch.setattr(repo, "update_user_password", lambda user_id, password_hash: saved.update({user_id: password_hash}))

    with app.test_client() as client:
        with client.session_transaction() as session:
            session["user_id"] = 1
            session["_csrf_token"] = "test-token"

        response = client.post(
            "/password",
            data={
                "_csrf_token": "test-token",
                "current_password": "admin123",
                "new_password": "nuevo1234",
                "confirm_password": "nuevo1234",
            },
        )

    assert response.status_code == 302
    assert 1 in saved
