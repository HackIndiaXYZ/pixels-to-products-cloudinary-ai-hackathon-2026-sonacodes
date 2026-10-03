from argon2 import PasswordHasher
from fastapi.testclient import TestClient

from app.auth_security import auth_rate_limiter
from app.database import SessionLocal
from app.main import app
from app.models import AuthSession, ClothingItem, User
from app.services.cloudinary_service import VerifiedAsset


def _csrf(client):
    response = client.get('/api/auth/csrf')
    assert response.status_code == 200
    return response.json()['csrf_token']


def _register(client, email='person@example.com', name='Person Name'):
    csrf = _csrf(client)
    response = client.post(
        '/api/auth/register',
        headers={'X-CSRF-Token': csrf},
        json={
            'name': name,
            'email': email,
            'password': 'Strong-Test-Password-123!',
            'confirm_password': 'Strong-Test-Password-123!',
        },
    )
    if response.status_code == 201:
        client.headers['X-CSRF-Token'] = response.json()['csrf_token']
    return response


def _create_item(client, user_id, slug, name):
    response = client.post(
        '/api/items',
        json={
            'name': name,
            'category': 'Tops',
            'colour': 'Blue',
            'pattern': 'Solid',
            'style': 'Casual',
            'occasion': 'Everyday',
            'cloudinary_public_id': f'wardrobeai/users/{user_id}/clothing/{slug}',
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_unauthenticated_users_cannot_access_product_apis():
    with TestClient(app) as client:
        assert client.get('/api/health').status_code == 200
        assert client.get('/api/items').status_code == 401
        assert client.get('/api/stats').status_code == 401
        assert client.get('/api/ai/capabilities').status_code == 401
        assert client.post('/api/uploads/signature').status_code == 401
        assert client.post('/api/ai/recommend-outfits', json={}).status_code == 401


def test_registration_normalizes_email_and_stores_argon_hash():
    auth_rate_limiter.clear()
    with TestClient(app) as client:
        response = _register(client, '  Person@Example.COM  ', '  A Person  ')
        assert response.status_code == 201, response.text
        body = response.json()
        assert body['user']['name'] == 'A Person'
        assert body['user']['email'] == 'person@example.com'
        assert 'password_hash' not in response.text
        assert client.cookies.get('wardrobeai_session')
        assert client.cookies.get('wardrobeai_csrf')
        set_cookie_headers = response.headers.get_list('set-cookie')
        assert any('wardrobeai_session=' in value and 'HttpOnly' in value for value in set_cookie_headers)
        session_cookie = client.cookies.get('wardrobeai_session')
        assert session_cookie

        db = SessionLocal()
        try:
            user = db.query(User).filter(User.email == 'person@example.com').one()
            assert user.password_hash != 'Strong-Test-Password-123!'
            assert user.password_hash.startswith('$argon2id$')
            assert PasswordHasher().verify(user.password_hash, 'Strong-Test-Password-123!')
            assert db.query(AuthSession).count() == 1
        finally:
            db.close()

        duplicate = client.post(
            '/api/auth/register',
            headers={'X-CSRF-Token': body['csrf_token']},
            json={
                'name': 'Another Person',
                'email': 'PERSON@example.com',
                'password': 'Strong-Test-Password-123!',
                'confirm_password': 'Strong-Test-Password-123!',
            },
        )
        assert duplicate.status_code == 409
        assert 'already exists' in duplicate.json()['detail']


def test_registration_validates_required_fields_email_strength_and_match():
    auth_rate_limiter.clear()
    cases = [
        ({'name': '   ', 'email': 'a@example.com', 'password': 'Strong-Test-Password-123!', 'confirm_password': 'Strong-Test-Password-123!'}, 422),
        ({'name': 'Person', 'email': 'invalid-email', 'password': 'Strong-Test-Password-123!', 'confirm_password': 'Strong-Test-Password-123!'}, 422),
        ({'name': 'Person', 'email': 'a@example.com', 'password': 'short', 'confirm_password': 'short'}, 422),
        ({'name': 'Person', 'email': 'a@example.com', 'password': 'Strong-Test-Password-123!', 'confirm_password': 'Different-Password-123!'}, 422),
    ]
    with TestClient(app) as client:
        csrf = _csrf(client)
        for payload, expected_status in cases:
            response = client.post('/api/auth/register', headers={'X-CSRF-Token': csrf}, json=payload)
            assert response.status_code == expected_status, response.text


def test_login_generic_error_logout_and_session_invalidation():
    auth_rate_limiter.clear()
    with TestClient(app) as client:
        registration = _register(client)
        assert registration.status_code == 201
        client.cookies.clear()
        csrf = _csrf(client)
        unknown = client.post(
            '/api/auth/login',
            headers={'X-CSRF-Token': csrf},
            json={'email': 'missing@example.com', 'password': 'Wrong-Password-123!'},
        )
        invalid = client.post(
            '/api/auth/login',
            headers={'X-CSRF-Token': csrf},
            json={'email': 'person@example.com', 'password': 'Wrong-Password-123!'},
        )
        assert unknown.status_code == invalid.status_code == 401
        assert unknown.json()['detail'] == invalid.json()['detail'] == 'Invalid email or password.'

        login = client.post(
            '/api/auth/login',
            headers={'X-CSRF-Token': csrf},
            json={'email': 'PERSON@example.com', 'password': 'Strong-Test-Password-123!'},
        )
        assert login.status_code == 200
        csrf_after_login = login.json()['csrf_token']
        assert client.get('/api/auth/me').json()['email'] == 'person@example.com'
        logout = client.post('/api/auth/logout', headers={'X-CSRF-Token': csrf_after_login})
        assert logout.status_code == 204
        assert client.get('/api/auth/me').status_code == 401
        assert client.get('/api/items').status_code == 401


def test_inactive_user_cannot_sign_in(client):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == 'test@example.com').one()
        user.is_active = False
        db.commit()
    finally:
        db.close()

    client.cookies.clear()
    csrf = _csrf(client)
    response = client.post(
        '/api/auth/login',
        headers={'X-CSRF-Token': csrf},
        json={'email': 'test@example.com', 'password': 'Strong-Test-Password-123!'},
    )
    assert response.status_code == 401
    assert response.json()['detail'] == 'Invalid email or password.'


def test_two_users_cannot_access_each_others_wardrobes_or_assets(client, monkeypatch):
    monkeypatch.setattr(
        'app.services.item_service.verify_asset',
        lambda public_id, _user_id: VerifiedAsset(
            public_id=public_id,
            secure_url=f'https://res.cloudinary.com/test-cloud/image/upload/{public_id}.jpg',
            bytes=512,
            format='jpg',
        ),
    )
    user_a_item = _create_item(client, 1, 'person-a-shirt', 'Person A shirt')
    destroyed = []
    monkeypatch.setattr(
        'app.services.item_service.destroy_asset',
        lambda public_id, user_id: destroyed.append((public_id, user_id)) or 'ok',
    )

    with TestClient(app) as client_b:
        registration_b = _register(client_b, 'person-b@example.com', 'Person B')
        assert registration_b.status_code == 201, registration_b.text
        user_b_id = registration_b.json()['user']['id']
        user_b_item = _create_item(client_b, user_b_id, 'person-b-shirt', 'Person B shirt')

        assert [item['id'] for item in client.get('/api/items').json()['items']] == [user_a_item['id']]
        assert [item['id'] for item in client_b.get('/api/items').json()['items']] == [user_b_item['id']]
        assert client.get(f"/api/items/{user_b_item['id']}").status_code == 404
        assert client.put(f"/api/items/{user_b_item['id']}", json={'name': 'Stolen'}).status_code == 404
        assert client.delete(f"/api/items/{user_b_item['id']}").status_code == 404
        assert client_b.get(f"/api/items/{user_a_item['id']}").status_code == 404
        assert client_b.put(f"/api/items/{user_a_item['id']}", json={'name': 'Stolen'}).status_code == 404
        assert client_b.delete(f"/api/items/{user_a_item['id']}").status_code == 404
        assert client.get('/api/stats').json()['total_items'] == 1
        assert client_b.get('/api/stats').json()['total_items'] == 1

        foreign_discard = client.post(
            '/api/uploads/discard',
            json={'public_id': user_b_item['cloudinary_public_id']},
        )
        assert foreign_discard.status_code == 404
        assert destroyed == []

        captured_ids = []

        def no_recommendations(items, *_args, **_kwargs):
            captured_ids.extend(item.id for item in items)
            return []

        monkeypatch.setattr('app.routers.ai.get_recommendations_for_request', no_recommendations)
        recommendation = client.post('/api/ai/recommend-outfits', json={'occasion': 'Everyday'})
        assert recommendation.status_code == 200
        assert captured_ids == [user_a_item['id']]


def test_state_changing_requests_require_csrf(client, monkeypatch):
    csrf_header = client.headers.pop('X-CSRF-Token')
    response = client.post(
        '/api/items',
        json={
            'name': 'No CSRF',
            'category': 'Tops',
            'colour': 'Blue',
            'pattern': 'Solid',
            'style': 'Casual',
            'occasion': 'Everyday',
            'cloudinary_public_id': 'wardrobeai/users/1/clothing/no-csrf',
        },
    )
    assert response.status_code == 403
    client.headers['X-CSRF-Token'] = csrf_header


def test_cloudinary_asset_folder_cannot_be_spoofed_between_users(client, monkeypatch):
    def cloudinary_must_not_be_called():
        raise AssertionError('foreign user asset must be rejected before Cloudinary lookup')

    monkeypatch.setattr('app.services.cloudinary_service._configure', cloudinary_must_not_be_called)
    response = client.post(
        '/api/items',
        json={
            'name': 'Foreign',
            'category': 'Tops',
            'colour': 'Blue',
            'pattern': 'Solid',
            'style': 'Casual',
            'occasion': 'Everyday',
            'cloudinary_public_id': 'wardrobeai/users/2/clothing/foreign',
        },
    )
    assert response.status_code == 400
    assert response.json()['error']['code'] == 'invalid_asset'
