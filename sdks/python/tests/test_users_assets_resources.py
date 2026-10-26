"""Tests for UsersResource and AssetsResource (folders and files)."""

from __future__ import annotations

import json

import httpx
import pytest
from helpers import json_response

from nova_sdk import schemas
from nova_sdk.exceptions import NovaNotFoundError, NovaValidationError

FOLDER_ID = "44444444-4444-4444-4444-444444444444"
FILE_ID = "55555555-5555-5555-5555-555555555555"


def _page(results):
    return {
        "pagination": {
            "count": len(results),
            "page": 1,
            "total_pages": 1,
            "page_size": 20,
        },
        "results": results,
    }


def test_users_list_and_me(mock_client_factory):
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/v1/users/":
            assert request.url.params["page_size"] == "5"
            return json_response(data=_page([{"id": "u1", "email": "a@b.co"}]))
        assert request.url.path == "/api/v1/users/me/"
        return json_response(
            data={"id": "u1", "email": "a@b.co", "current_role": "VIEWER"}
        )

    client = mock_client_factory(handler, api_key="nova_key_test")
    users = client.users.list(page_size=5)
    assert isinstance(users[0], schemas.User)
    me = client.users.me()
    assert isinstance(me, schemas.UserMe)
    assert me.current_role == "VIEWER"


def test_folders_crud(mock_client_factory):
    seen = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.method, request.url.path))
        if request.method == "GET" and request.url.path.endswith("/folders/"):
            assert request.url.params["search"] == "logos"
            return json_response(data=_page([{"id": FOLDER_ID, "name": "Logos"}]))
        if request.method == "POST":
            assert json.loads(request.content) == {"name": "Logos"}
            return json_response(
                status_code=201, data={"id": FOLDER_ID, "name": "Logos"}
            )
        if request.method == "PATCH":
            assert json.loads(request.content) == {"name": "Brand"}
            return json_response(data={"id": FOLDER_ID, "name": "Brand"})
        if request.method == "DELETE":
            return httpx.Response(204)
        return json_response(data={"id": FOLDER_ID, "name": "Logos"})

    client = mock_client_factory(handler, api_key="nova_key_test")
    assert client.assets.folders.list(search="logos")[0].name == "Logos"
    assert isinstance(client.assets.folders.create(name="Logos"), schemas.AssetFolder)
    assert client.assets.folders.get(FOLDER_ID).id == FOLDER_ID
    assert client.assets.folders.update(FOLDER_ID, name="Brand").name == "Brand"
    assert client.assets.folders.delete(FOLDER_ID) is None
    assert ("DELETE", f"/api/v1/assets/folders/{FOLDER_ID}/") in seen


def test_file_upload_from_bytes_sends_multipart(mock_client_factory):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/api/v1/assets/files/upload/"
        assert request.headers["content-type"].startswith("multipart/form-data")
        body = request.content
        assert b'name="file"; filename="logo.png"' in body
        assert b"Content-Type: image/png" in body
        assert b'name="folder"' in body and FOLDER_ID.encode() in body
        return json_response(
            status_code=201,
            data={"id": FILE_ID, "name": "logo.png", "mime_type": "image/png"},
        )

    client = mock_client_factory(handler, api_key="nova_key_test")
    asset = client.assets.files.upload(
        b"\x89PNGdata", filename="logo.png", folder=FOLDER_ID
    )
    assert isinstance(asset, schemas.MediaAsset)
    assert asset.mime_type == "image/png"


def test_file_upload_from_path_infers_filename(mock_client_factory, tmp_path):
    path = tmp_path / "banner.jpg"
    path.write_bytes(b"jpgdata")

    def handler(request: httpx.Request) -> httpx.Response:
        assert b'filename="banner.jpg"' in request.content
        assert b"Content-Type: image/jpeg" in request.content
        return json_response(
            status_code=201, data={"id": FILE_ID, "name": "banner.jpg"}
        )

    client = mock_client_factory(handler, api_key="nova_key_test")
    assert client.assets.files.upload(path).name == "banner.jpg"


def test_file_upload_from_stream(mock_client_factory, tmp_path):
    path = tmp_path / "doc.pdf"
    path.write_bytes(b"%PDF-1")

    def handler(request: httpx.Request) -> httpx.Response:
        assert b'filename="doc.pdf"' in request.content
        return json_response(status_code=201, data={"id": FILE_ID})

    client = mock_client_factory(handler, api_key="nova_key_test")
    with path.open("rb") as fh:
        client.assets.files.upload(fh)


def test_file_create_with_display_name(mock_client_factory):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/v1/assets/files/"
        assert b'name="name"' in request.content and b"Hero" in request.content
        return json_response(status_code=201, data={"id": FILE_ID, "name": "Hero"})

    client = mock_client_factory(handler, api_key="nova_key_test")
    assert (
        client.assets.files.create(b"x", filename="a.png", name="Hero").name == "Hero"
    )


@pytest.mark.parametrize(
    "file,kwargs",
    [
        (b"", {"filename": "a.png"}),
        (b"data", {}),
        (12345, {"filename": "a.png"}),
        ("/definitely/not/a/file.png", {}),
    ],
)
def test_file_upload_validation(mock_client_factory, file, kwargs):
    client = mock_client_factory(lambda r: json_response(), api_key="nova_key_test")
    with pytest.raises(NovaValidationError):
        client.assets.files.upload(file, **kwargs)


def test_file_update_requires_a_field(mock_client_factory):
    client = mock_client_factory(lambda r: json_response(), api_key="nova_key_test")
    with pytest.raises(NovaValidationError):
        client.assets.files.update(FILE_ID)


def test_file_update_get_delete_and_not_found(mock_client_factory):
    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "PATCH":
            assert request.headers["content-type"].startswith(
                "application/x-www-form-urlencoded"
            )
            assert b"name=renamed" in request.content
            return json_response(data={"id": FILE_ID, "name": "renamed"})
        if request.method == "DELETE":
            return httpx.Response(204)
        if request.url.path.endswith("missing/"):
            return json_response(
                status_code=404, message="Not found", error_code="NOT_FOUND"
            )
        return json_response(data={"id": FILE_ID, "name": "a"})

    client = mock_client_factory(handler, api_key="nova_key_test")
    assert client.assets.files.update(FILE_ID, name="renamed").name == "renamed"
    assert client.assets.files.get(FILE_ID).id == FILE_ID
    assert client.assets.files.delete(FILE_ID) is None
    with pytest.raises(NovaNotFoundError):
        client.assets.files.get("missing")
