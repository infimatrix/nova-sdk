"""Media asset (folders and files) resource clients for Nova SDK."""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any
from urllib.parse import quote

from nova_sdk._model_base import parse_model
from nova_sdk.exceptions import NovaValidationError
from nova_sdk.models import PaginatedResponse
from nova_sdk.resources._files import FileInput, build_file_part
from nova_sdk.resources.base import BaseResource
from nova_sdk.schemas import AssetFolder, MediaAsset

if TYPE_CHECKING:
    from nova_sdk.http import HTTPTransport


def _clean_id(value: str, label: str) -> str:
    if not value or not str(value).strip():
        raise NovaValidationError(f"{label} must be a non-empty string.")
    return str(value).strip()


def _path_id(value: str, label: str) -> str:
    """Validate a path identifier and URL-encode it."""
    return quote(_clean_id(value, label), safe="")


def _list_params(
    search: str | None,
    ordering: str | None,
    page: int | None,
    page_size: int | None,
    params: Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    query: dict[str, Any] = dict(params or {})
    for key, value in (
        ("search", search),
        ("ordering", ordering),
        ("page", page),
        ("page_size", page_size),
    ):
        if value is not None:
            query[key] = value
    return query or None


class AssetFoldersResource(BaseResource):
    """Resource client for media asset folders."""

    def list(
        self,
        *,
        search: str | None = None,
        ordering: str | None = None,
        page: int | None = None,
        page_size: int | None = None,
        params: Mapping[str, Any] | None = None,
        tenant_id: str | None = None,
    ) -> PaginatedResponse[AssetFolder]:
        """List asset folders. Endpoint: GET /api/v1/assets/folders/"""
        response = self._transport.request(
            "GET",
            "assets/folders/",
            params=_list_params(search, ordering, page, page_size, params),
            tenant_id=tenant_id,
        )
        return PaginatedResponse.from_response(
            response, item_parser=AssetFolder.from_dict
        )

    def get(self, folder_id: str, *, tenant_id: str | None = None) -> AssetFolder:
        """Retrieve a folder. Endpoint: GET /api/v1/assets/folders/{id}/"""
        clean_id = _path_id(folder_id, "folder_id")
        response = self._transport.request(
            "GET", f"assets/folders/{clean_id}/", tenant_id=tenant_id
        )
        return parse_model(AssetFolder, response.data or {})

    def create(self, *, name: str, tenant_id: str | None = None) -> AssetFolder:
        """Create a folder. Endpoint: POST /api/v1/assets/folders/"""
        response = self._transport.request(
            "POST",
            "assets/folders/",
            json={"name": _clean_id(name, "name")},
            tenant_id=tenant_id,
        )
        return parse_model(AssetFolder, response.data or {})

    def update(
        self, folder_id: str, *, name: str, tenant_id: str | None = None
    ) -> AssetFolder:
        """Rename a folder. Endpoint: PATCH /api/v1/assets/folders/{id}/"""
        clean_id = _path_id(folder_id, "folder_id")
        response = self._transport.request(
            "PATCH",
            f"assets/folders/{clean_id}/",
            json={"name": _clean_id(name, "name")},
            tenant_id=tenant_id,
        )
        return parse_model(AssetFolder, response.data or {})

    def delete(self, folder_id: str, *, tenant_id: str | None = None) -> None:
        """Delete a folder. Endpoint: DELETE /api/v1/assets/folders/{id}/"""
        clean_id = _path_id(folder_id, "folder_id")
        self._transport.request(
            "DELETE", f"assets/folders/{clean_id}/", tenant_id=tenant_id
        )


class AssetFilesResource(BaseResource):
    """Resource client for uploaded media files."""

    def list(
        self,
        *,
        search: str | None = None,
        ordering: str | None = None,
        page: int | None = None,
        page_size: int | None = None,
        params: Mapping[str, Any] | None = None,
        tenant_id: str | None = None,
    ) -> PaginatedResponse[MediaAsset]:
        """List uploaded files. Endpoint: GET /api/v1/assets/files/"""
        response = self._transport.request(
            "GET",
            "assets/files/",
            params=_list_params(search, ordering, page, page_size, params),
            tenant_id=tenant_id,
        )
        return PaginatedResponse.from_response(
            response, item_parser=MediaAsset.from_dict
        )

    def get(self, file_id: str, *, tenant_id: str | None = None) -> MediaAsset:
        """Retrieve file metadata. Endpoint: GET /api/v1/assets/files/{id}/"""
        clean_id = _path_id(file_id, "file_id")
        response = self._transport.request(
            "GET", f"assets/files/{clean_id}/", tenant_id=tenant_id
        )
        return parse_model(MediaAsset, response.data or {})

    def upload(
        self,
        file: FileInput,
        *,
        folder: str | None = None,
        filename: str | None = None,
        content_type: str | None = None,
        tenant_id: str | None = None,
    ) -> MediaAsset:
        """Upload a file. Endpoint: POST /api/v1/assets/files/upload/

        Args:
            file: Bytes, a filesystem path, or a readable binary stream.
            folder: Optional destination folder ID.
            filename: Filename to send (required for raw bytes; inferred from paths).
            content_type: MIME type; guessed from the filename when omitted.
            tenant_id: Optional explicit tenant UUID override.
        """
        part = build_file_part(file, filename=filename, content_type=content_type)
        data = {"folder": _clean_id(folder, "folder")} if folder is not None else None
        response = self._transport.request(
            "POST",
            "assets/files/upload/",
            files={"file": part},
            data=data,
            tenant_id=tenant_id,
        )
        return parse_model(MediaAsset, response.data or {})

    def create(
        self,
        file: FileInput,
        *,
        name: str,
        folder: str | None = None,
        filename: str | None = None,
        content_type: str | None = None,
        tenant_id: str | None = None,
    ) -> MediaAsset:
        """Upload a file with an explicit display name.

        Endpoint: POST /api/v1/assets/files/
        """
        part = build_file_part(file, filename=filename, content_type=content_type)
        data: dict[str, Any] = {"name": _clean_id(name, "name")}
        if folder is not None:
            data["folder"] = _clean_id(folder, "folder")
        response = self._transport.request(
            "POST",
            "assets/files/",
            files={"file": part},
            data=data,
            tenant_id=tenant_id,
        )
        return parse_model(MediaAsset, response.data or {})

    def update(
        self,
        file_id: str,
        *,
        name: str | None = None,
        folder: str | None = None,
        tenant_id: str | None = None,
    ) -> MediaAsset:
        """Rename or move a file. Endpoint: PATCH /api/v1/assets/files/{id}/"""
        clean_id = _path_id(file_id, "file_id")
        data: dict[str, Any] = {}
        if name is not None:
            data["name"] = _clean_id(name, "name")
        if folder is not None:
            data["folder"] = _clean_id(folder, "folder")
        if not data:
            raise NovaValidationError("Provide at least one of name or folder.")
        response = self._transport.request(
            "PATCH",
            f"assets/files/{clean_id}/",
            data=data,
            tenant_id=tenant_id,
        )
        return parse_model(MediaAsset, response.data or {})

    def delete(self, file_id: str, *, tenant_id: str | None = None) -> None:
        """Delete a file. Endpoint: DELETE /api/v1/assets/files/{id}/"""
        clean_id = _path_id(file_id, "file_id")
        self._transport.request(
            "DELETE", f"assets/files/{clean_id}/", tenant_id=tenant_id
        )


class AssetsResource(BaseResource):
    """Resource client for the media library (folders and files)."""

    def __init__(self, transport: HTTPTransport, client: Any = None) -> None:
        super().__init__(transport)
        self._client = client
        self.folders = AssetFoldersResource(transport)
        self.files = AssetFilesResource(transport)
