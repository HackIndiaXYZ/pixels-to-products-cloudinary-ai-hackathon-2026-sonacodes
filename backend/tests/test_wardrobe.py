"""Validation, CRUD, filtering, and Cloudinary failure behaviour."""

import cloudinary.utils
from sqlalchemy import inspect

from app.config import Settings
from app.database import _sqlalchemy_database_url, engine
from app.errors import CloudinaryUnavailable, InvalidAsset
from app.services.cloudinary_service import VerifiedAsset


def _payload(**overrides):
    data = {
        "name": "Ivory shirt",
        "category": "Tops",
        "colour": "Ivory",
        "pattern": "Solid",
        "style": "Minimal",
        "occasion": "Work",
        "cloudinary_public_id": "wardrobeai/items/ivory-shirt",
    }
    data.update(overrides)
    if data["cloudinary_public_id"].startswith("wardrobeai/items/"):
        suffix = data["cloudinary_public_id"].rsplit("/", 1)[-1]
        data["cloudinary_public_id"] = f"wardrobeai/users/1/clothing/{suffix}"
    return data


def _asset(public_id: str, size: int = 2048) -> VerifiedAsset:
    return VerifiedAsset(
        public_id=public_id,
        secure_url=f"https://res.cloudinary.com/test-cloud/image/upload/{public_id}.jpg",
        bytes=size,
        format="jpg",
    )


def _create(client, monkeypatch, **overrides):
    payload = _payload(**overrides)
    monkeypatch.setattr(
        "app.services.item_service.verify_asset",
        lambda public_id, _user_id: _asset(public_id),
    )
    response = client.post("/api/items", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def test_clothing_table_has_phase_one_columns(client):
    del client
    columns = {column["name"] for column in inspect(engine).get_columns("clothing_items")}
    assert {
        "id",
        "name",
        "category",
        "subcategory",
        "colour",
        "secondary_colour",
        "pattern",
        "style",
        "occasion",
        "season",
        "brand",
        "notes",
        "cloudinary_public_id",
        "secure_url",
        "created_at",
        "updated_at",
    } <= columns


def test_health_reports_configuration(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["database"] == "ok"
    assert body["cloudinary_configured"] is True
    assert body["cloud_name"] == "test-cloud"
    assert "api_secret" not in response.text
    assert "test-secret-value" not in response.text


def test_root_health_alias_and_postgres_url_normalization(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["database"] == "ok"
    assert _sqlalchemy_database_url("postgres://user:pass@host/db") == (
        "postgresql+psycopg://user:pass@host/db"
    )
    assert _sqlalchemy_database_url("postgresql://user:pass@host/db") == (
        "postgresql+psycopg://user:pass@host/db"
    )


def test_health_when_cloudinary_is_missing(client, monkeypatch):
    monkeypatch.setattr(
        "app.routers.health.get_settings",
        lambda: Settings(
            database_url="sqlite://",
            cloudinary_cloud_name="",
            cloudinary_api_key="",
            cloudinary_api_secret="",
        ),
    )
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["cloudinary_configured"] is False
    assert body["cloud_name"] is None


def test_signature_matches_signed_params_and_hides_secret(client):
    response = client.post("/api/uploads/signature")
    assert response.status_code == 200
    body = response.json()
    assert body["folder"] == "wardrobeai/users/1/clothing"
    assert body["allowed_formats"] == "jpg,png,webp"
    assert body["api_key"] == "123456789012345"
    assert "test-secret-value" not in response.text
    expected = cloudinary.utils.api_sign_request(
        {
            "timestamp": body["timestamp"],
            "folder": body["folder"],
            "allowed_formats": body["allowed_formats"],
        },
        "test-secret-value",
    )
    assert body["signature"] == expected
    assert body["upload_url"] == "https://api.cloudinary.com/v1_1/test-cloud/image/upload"


def test_signature_when_cloudinary_is_missing(client, monkeypatch):
    monkeypatch.setattr(
        "app.services.cloudinary_service.get_settings",
        lambda: Settings(
            database_url="sqlite://",
            cloudinary_cloud_name="",
            cloudinary_api_key="",
            cloudinary_api_secret="",
        ),
    )
    response = client.post("/api/uploads/signature")
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "cloudinary_not_configured"


def test_create_rejects_unknown_category(client):
    response = client.post("/api/items", json=_payload(category="Hats"))
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_create_rejects_public_id_outside_folder(client, monkeypatch):
    called = False

    def _verify(_public_id):
        nonlocal called
        called = True
        raise AssertionError("verify should not run")

    monkeypatch.setattr("app.services.item_service.verify_asset", _verify)
    response = client.post(
        "/api/items",
        json=_payload(cloudinary_public_id="https://res.cloudinary.com/other/image/upload/x"),
    )
    assert response.status_code == 422
    assert called is False


def test_create_rejects_asset_cloudinary_does_not_confirm(client, monkeypatch):
    def _reject(_public_id: str, _user_id: int) -> VerifiedAsset:
        raise InvalidAsset("Image must be a JPEG, PNG, or WebP file up to 10 MB.")

    monkeypatch.setattr("app.services.item_service.verify_asset", _reject)
    response = client.post("/api/items", json=_payload())
    assert response.status_code == 400
    assert "10 MB" in response.json()["error"]["message"]
    assert client.get("/api/items").json()["total"] == 0


def test_create_stores_url_from_verified_asset_not_client(client, monkeypatch):
    monkeypatch.setattr(
        "app.services.item_service.verify_asset",
        lambda public_id, _user_id: _asset(public_id),
    )
    response = client.post(
        "/api/items",
        json=_payload(secure_url="https://evil.example/image.jpg"),
    )
    assert response.status_code == 201
    body = response.json()
    assert body["secure_url"].startswith("https://res.cloudinary.com/test-cloud/")
    assert "evil.example" not in body["secure_url"]
    assert body["cloudinary_public_id"] == "wardrobeai/users/1/clothing/ivory-shirt"


def test_duplicate_public_id_conflicts(client, monkeypatch):
    _create(client, monkeypatch)
    monkeypatch.setattr(
        "app.services.item_service.verify_asset",
        lambda public_id, _user_id: _asset(public_id),
    )
    response = client.post("/api/items", json=_payload(name="Another shirt"))
    assert response.status_code == 409


def test_search_and_filters_combine(client, monkeypatch):
    _create(client, monkeypatch, name="Ivory shirt", colour="Ivory", brand="Arket", style="Minimal")
    _create(
        client,
        monkeypatch,
        name="Navy trouser",
        category="Bottoms",
        colour="Navy",
        pattern="Solid",
        style="Classic",
        occasion="Work",
        brand="Arket",
        cloudinary_public_id="wardrobeai/items/navy-trouser",
    )
    _create(
        client,
        monkeypatch,
        name="Ivory skirt",
        category="Bottoms",
        colour="Ivory",
        pattern="Solid",
        style="Minimal",
        occasion="Weekend",
        brand="Cos",
        cloudinary_public_id="wardrobeai/items/ivory-skirt",
    )

    response = client.get(
        "/api/items",
        params={"q": "arket", "category": "Bottoms", "colour": "navy", "style": "Classic"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["name"] == "Navy trouser"

    by_name = client.get("/api/items", params={"q": "ivory", "sort": "name"})
    names = [item["name"] for item in by_name.json()["items"]]
    assert names == ["Ivory shirt", "Ivory skirt"]


def test_pagination(client, monkeypatch):
    _create(client, monkeypatch, name="Alpha", cloudinary_public_id="wardrobeai/items/alpha")
    _create(client, monkeypatch, name="Beta", cloudinary_public_id="wardrobeai/items/beta")
    page = client.get("/api/items", params={"page": 2, "page_size": 1, "sort": "name"})
    body = page.json()
    assert body["total"] == 2
    assert body["pages"] == 2
    assert [item["name"] for item in body["items"]] == ["Beta"]


def test_get_update_and_missing_item(client, monkeypatch):
    created = _create(client, monkeypatch, notes="Soft cotton")
    fetched = client.get(f"/api/items/{created['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["notes"] == "Soft cotton"

    updated = client.put(
        f"/api/items/{created['id']}",
        json={"name": "Ivory poplin shirt", "colour": "Cream", "season": "Summer", "brand": "Toteme"},
    )
    assert updated.status_code == 200
    body = updated.json()
    assert body["name"] == "Ivory poplin shirt"
    assert body["colour"] == "Cream"
    assert body["season"] == "Summer"
    assert body["brand"] == "Toteme"
    assert body["cloudinary_public_id"] == created["cloudinary_public_id"]

    missing = client.get("/api/items/999")
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "not_found"


def test_stats_come_from_stored_items(client, monkeypatch):
    _create(client, monkeypatch, category="Tops", colour="Ivory")
    _create(
        client,
        monkeypatch,
        name="Coat",
        category="Outerwear",
        colour="Camel",
        cloudinary_public_id="wardrobeai/items/coat",
    )
    _create(
        client,
        monkeypatch,
        name="Knit",
        category="Tops",
        colour="Ivory",
        cloudinary_public_id="wardrobeai/items/knit",
    )
    body = client.get("/api/stats").json()
    assert body["total_items"] == 3
    assert body["category_count"] == 2
    assert body["top_category"] == "Tops"
    assert body["top_category_count"] == 2
    assert body["colours"] == ["Camel", "Ivory"]
    assert len(body["recent_items"]) == 3
    assert body["recent_items"][0]["name"] == "Knit"


def test_delete_removes_row_after_cloudinary_success(client, monkeypatch):
    created = _create(client, monkeypatch)
    destroyed = []
    monkeypatch.setattr(
        "app.services.item_service.destroy_asset",
        lambda public_id, _user_id: destroyed.append(public_id) or "ok",
    )
    response = client.delete(f"/api/items/{created['id']}")
    assert response.status_code == 204
    assert destroyed == ["wardrobeai/users/1/clothing/ivory-shirt"]
    assert client.get(f"/api/items/{created['id']}").status_code == 404


def test_delete_keeps_row_when_cloudinary_fails(client, monkeypatch):
    created = _create(client, monkeypatch)

    def _fail(_public_id, _user_id):
        raise CloudinaryUnavailable("The clothing image could not be deleted from Cloudinary. The wardrobe item was kept.")

    monkeypatch.setattr("app.services.item_service.destroy_asset", _fail)
    response = client.delete(f"/api/items/{created['id']}")
    assert response.status_code == 502
    assert client.get(f"/api/items/{created['id']}").status_code == 200


def test_delete_treats_missing_cloudinary_asset_as_success(client, monkeypatch):
    created = _create(client, monkeypatch)
    monkeypatch.setattr("app.services.item_service.destroy_asset", lambda _public_id, _user_id: "not found")
    response = client.delete(f"/api/items/{created['id']}")
    assert response.status_code == 204
    assert client.get("/api/items").json()["total"] == 0


def test_discard_unsaved_upload(client, monkeypatch):
    destroyed = []
    monkeypatch.setattr(
        "app.services.item_service.destroy_asset",
        lambda public_id, _user_id: destroyed.append(public_id) or "ok",
    )
    response = client.post("/api/uploads/discard", json={"public_id": "wardrobeai/users/1/clothing/orphan"})
    assert response.status_code == 204
    assert destroyed == ["wardrobeai/users/1/clothing/orphan"]


def test_discard_does_not_remove_saved_item(client, monkeypatch):
    created = _create(client, monkeypatch)

    def _fail(_public_id, _user_id):
        raise AssertionError("destroy should not run")

    monkeypatch.setattr("app.services.item_service.destroy_asset", _fail)
    response = client.post(
        "/api/uploads/discard",
        json={"public_id": created["cloudinary_public_id"]},
    )
    assert response.status_code == 409
    assert client.get(f"/api/items/{created['id']}").status_code == 200


def test_empty_stats(client):
    body = client.get("/api/stats").json()
    assert body["total_items"] == 0
    assert body["category_count"] == 0
    assert body["top_category"] is None
    assert body["recent_items"] == []


def test_ai_capabilities_report_cloudinary_status(client):
    response = client.get("/api/ai/capabilities")
    assert response.status_code == 200
    body = response.json()
    assert body["cloudinary"]["configured"] is True
    assert body["cloudinary"]["image_transformations"] == "available"
    assert body["cloudinary"]["layered_composition"] == "available"
    assert body["external_ai_providers"] is False


def test_ai_recognition_valid_response(client, monkeypatch):
    created = _create(client, monkeypatch, cloudinary_public_id="wardrobeai/items/white-shirt")
    class DummyProvider:
        provider_name = "cloudinary"

        def recognize_clothing(self, *_args, **_kwargs):
            return {
                "item_name": "White shirt",
                "category": "Tops",
                "subcategory": "Shirt",
                "primary_colour": "White",
                "secondary_colour": None,
                "pattern": "Solid",
                "material": "Cotton",
                "texture": "Smooth",
                "sleeve_type": "Short sleeve",
                "neckline": "Crew neck",
                "fit": "Regular",
                "length": "Hip length",
                "style": ["Casual"],
                "occasions": ["Everyday"],
                "seasons": ["Summer"],
                "formality": "Casual",
                "description": "A simple white shirt.",
                "tags": ["white", "shirt"],
                "confidence": {"category": 0.97, "primary_colour": 0.94, "pattern": 0.9},
            }

    monkeypatch.setattr("app.routers.ai.get_ai_provider", lambda: DummyProvider())
    response = client.post(
        "/api/ai/recognize-clothing",
        json={
            "cloudinary_public_id": created["cloudinary_public_id"],
            "secure_url": "https://res.cloudinary.com/test-cloud/image/upload/wardrobeai/items/white-shirt.jpg",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "cloudinary"
    assert body["recognition"]["category"] == "Tops"
    assert body["recognition"]["item_name"] == "White shirt"


def test_ai_recognition_rejects_invalid_json(monkeypatch, client):
    created = _create(client, monkeypatch, cloudinary_public_id="wardrobeai/items/bad")
    class DummyProvider:
        provider_name = "gemini"

        def recognize_clothing(self, *_args, **_kwargs):
            return "not-json"

    monkeypatch.setattr("app.routers.ai.get_ai_provider", lambda: DummyProvider())
    response = client.post(
        "/api/ai/recognize-clothing",
        json={
            "cloudinary_public_id": created["cloudinary_public_id"],
            "secure_url": "https://res.cloudinary.com/test-cloud/image/upload/wardrobeai/items/bad.jpg",
        },
    )
    assert response.status_code == 422


def test_ai_recognition_rejects_invalid_category(monkeypatch, client):
    created = _create(client, monkeypatch, cloudinary_public_id="wardrobeai/items/hat")
    class DummyProvider:
        provider_name = "gemini"

        def recognize_clothing(self, *_args, **_kwargs):
            return {"item_name": "Hat", "category": "Invalid", "primary_colour": "Blue"}

    monkeypatch.setattr("app.routers.ai.get_ai_provider", lambda: DummyProvider())
    response = client.post(
        "/api/ai/recognize-clothing",
        json={
            "cloudinary_public_id": created["cloudinary_public_id"],
            "secure_url": "https://res.cloudinary.com/test-cloud/image/upload/wardrobeai/items/hat.jpg",
        },
    )
    assert response.status_code == 422


def test_ai_recognition_rejects_untrusted_image(client):
    response = client.post(
        "/api/ai/recognize-clothing",
        json={"cloudinary_public_id": "external/hello", "secure_url": "https://evil.example/image.jpg"},
    )
    assert response.status_code == 404


def test_ai_recommendations_include_cloudinary_composition_url(client, monkeypatch):
    monkeypatch.setattr(
        "app.services.item_service.verify_asset",
        lambda public_id, _user_id: type("Asset", (), {"public_id": public_id, "secure_url": f"https://res.cloudinary.com/test-cloud/image/upload/{public_id}.jpg"})(),
    )

    def _create_item(payload):
        suffix = payload["cloudinary_public_id"].rsplit("/", 1)[-1]
        payload["cloudinary_public_id"] = f"wardrobeai/users/1/clothing/{suffix}"
        response = client.post("/api/items", json=payload)
        assert response.status_code == 201
        return response.json()

    _create_item(
        {
            "name": "White shirt",
            "category": "Tops",
            "colour": "White",
            "pattern": "Solid",
            "style": "Casual",
            "occasion": "Everyday",
            "cloudinary_public_id": "wardrobeai/items/white-shirt",
        }
    )
    _create_item(
        {
            "name": "Blue jeans",
            "category": "Bottoms",
            "colour": "Blue",
            "pattern": "Solid",
            "style": "Casual",
            "occasion": "Everyday",
            "cloudinary_public_id": "wardrobeai/items/blue-jeans",
        }
    )
    _create_item(
        {
            "name": "White sneakers",
            "category": "Shoes",
            "colour": "White",
            "pattern": "Solid",
            "style": "Casual",
            "occasion": "Everyday",
            "cloudinary_public_id": "wardrobeai/items/white-sneakers",
        }
    )

    class DummyProvider:
        provider_name = "cloudinary"

        def recommend_outfits(self, *_args, **_kwargs):
            return {
                "recommendations": [
                    {
                        "title": "Street-ready casual",
                        "description": "Balanced and easy.",
                        "occasion": "Everyday",
                        "style": "Casual",
                        "item_ids": [1, 2, 3],
                        "styling_tips": ["Keep layers light."],
                        "reasoning": "The outfit is balanced.",
                        "compatibility_score": 88,
                    }
                ]
            }

    monkeypatch.setattr("app.routers.ai.get_ai_provider", lambda: DummyProvider())
    response = client.post("/api/ai/recommend-outfits", json={"occasion": "Everyday"})
    assert response.status_code == 200
    body = response.json()
    assert "composition_url" in body["recommendations"][0]
    composition_url = body["recommendations"][0]["composition_url"]
    assert "res.cloudinary.com/test-cloud" in composition_url
    assert "/l_wardrobeai:users:1:clothing:white-shirt" in composition_url
    assert "/fl_layer_apply/" in composition_url
    assert composition_url.endswith("/wardrobeai/users/1/clothing/white-shirt")


def test_ai_recommendations_valid_wardrobe(client, monkeypatch):
    monkeypatch.setattr(
        "app.services.item_service.verify_asset",
        lambda public_id, _user_id: type("Asset", (), {"public_id": public_id, "secure_url": f"https://res.cloudinary.com/test-cloud/image/upload/{public_id}.jpg"})(),
    )

    def _create_item(payload):
        suffix = payload["cloudinary_public_id"].rsplit("/", 1)[-1]
        payload["cloudinary_public_id"] = f"wardrobeai/users/1/clothing/{suffix}"
        response = client.post("/api/items", json=payload)
        assert response.status_code == 201
        return response.json()

    _create_item(
        {
            "name": "White shirt",
            "category": "Tops",
            "colour": "White",
            "pattern": "Solid",
            "style": "Smart casual",
            "occasion": "Work",
            "cloudinary_public_id": "wardrobeai/items/white-shirt",
        }
    )
    _create_item(
        {
            "name": "Navy trousers",
            "category": "Bottoms",
            "colour": "Navy",
            "pattern": "Solid",
            "style": "Smart casual",
            "occasion": "Work",
            "cloudinary_public_id": "wardrobeai/items/navy-trouser",
        }
    )
    _create_item(
        {
            "name": "Black loafers",
            "category": "Shoes",
            "colour": "Black",
            "pattern": "Solid",
            "style": "Smart casual",
            "occasion": "Work",
            "cloudinary_public_id": "wardrobeai/items/black-loafers",
        }
    )

    class DummyProvider:
        provider_name = "gemini"

        def recommend_outfits(self, *_args, **_kwargs):
            return {
                "recommendations": [
                    {
                        "title": "Smart Casual Office",
                        "description": "Clean and polished.",
                        "occasion": "Work",
                        "style": "Smart casual",
                        "item_ids": [1, 2, 3],
                        "styling_tips": ["Tuck the shirt in."],
                        "reasoning": "The palette is balanced.",
                        "compatibility_score": 92,
                    }
                ]
            }

    monkeypatch.setattr("app.routers.ai.get_ai_provider", lambda: DummyProvider())
    response = client.post(
        "/api/ai/recommend-outfits",
        json={"occasion": "Work", "preferred_style": "Smart casual"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert len(body["recommendations"]) == 1
    assert body["recommendations"][0]["items"][0]["name"] == "White shirt"


def test_ai_recommendations_reject_invalid_llm_item_ids(client, monkeypatch):
    monkeypatch.setattr(
        "app.services.item_service.verify_asset",
        lambda public_id, _user_id: type("Asset", (), {"public_id": public_id, "secure_url": f"https://res.cloudinary.com/test-cloud/image/upload/{public_id}.jpg"})(),
    )

    def _create_item(payload):
        suffix = payload["cloudinary_public_id"].rsplit("/", 1)[-1]
        payload["cloudinary_public_id"] = f"wardrobeai/users/1/clothing/{suffix}"
        response = client.post("/api/items", json=payload)
        assert response.status_code == 201
        return response.json()

    _create_item(
        {
            "name": "White shirt",
            "category": "Tops",
            "colour": "White",
            "pattern": "Solid",
            "style": "Casual",
            "occasion": "Everyday",
            "cloudinary_public_id": "wardrobeai/items/wshirt",
        }
    )
    _create_item(
        {
            "name": "Blue jeans",
            "category": "Bottoms",
            "colour": "Blue",
            "pattern": "Solid",
            "style": "Casual",
            "occasion": "Everyday",
            "cloudinary_public_id": "wardrobeai/items/blue-jeans",
        }
    )

    class DummyProvider:
        provider_name = "gemini"

        def recommend_outfits(self, *_args, **_kwargs):
            return {
                "recommendations": [
                    {
                        "item_ids": [9999],
                        "title": "Wrong",
                        "description": "Bad",
                        "occasion": "Everyday",
                        "style": "Casual",
                        "styling_tips": [],
                        "reasoning": "",
                        "compatibility_score": 70,
                    }
                ]
            }

    monkeypatch.setattr("app.routers.ai.get_ai_provider", lambda: DummyProvider())
    response = client.post("/api/ai/recommend-outfits", json={"occasion": "Everyday"})
    assert response.status_code == 422
