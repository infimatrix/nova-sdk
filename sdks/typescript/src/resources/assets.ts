import { NovaValidationError } from "../errors.js";
import { buildUpload, type FileInput, type FileUploadOptions } from "../files.js";
import type { HttpTransport, RequestOptions } from "../http.js";
import type { Page } from "../models.js";
import type { AssetFolder, AssetFolderRequest, MediaAsset, PatchedAssetFolderRequest } from "../schemas.js";
import { BaseResource, pathId, requireString, type ListQuery } from "./base.js";

/** Media library folders. */
export class AssetFoldersResource extends BaseResource {
  /** `GET /api/v1/assets/folders/` */
  list(query: ListQuery = {}, options: RequestOptions = {}): Promise<Page<AssetFolder>> {
    return this.listPage<AssetFolder>("assets/folders/", { ...query }, options);
  }

  /** `GET /api/v1/assets/folders/{id}/` */
  async get(folderId: string, options: RequestOptions = {}): Promise<AssetFolder> {
    const res = await this.http.request<AssetFolder>("GET", `assets/folders/${pathId(folderId, "folderId")}/`, options);
    return res.data;
  }

  /** `POST /api/v1/assets/folders/` */
  async create(body: AssetFolderRequest, options: RequestOptions = {}): Promise<AssetFolder> {
    const payload = { name: requireString(body.name, "name") };
    const res = await this.http.request<AssetFolder>("POST", "assets/folders/", { ...options, json: payload });
    return res.data;
  }

  /** `PATCH /api/v1/assets/folders/{id}/`: rename a folder. */
  async update(folderId: string, body: PatchedAssetFolderRequest, options: RequestOptions = {}): Promise<AssetFolder> {
    const payload = { name: requireString(body.name, "name") };
    const res = await this.http.request<AssetFolder>("PATCH", `assets/folders/${pathId(folderId, "folderId")}/`, {
      ...options,
      json: payload,
    });
    return res.data;
  }

  /** `DELETE /api/v1/assets/folders/{id}/` */
  async delete(folderId: string, options: RequestOptions = {}): Promise<void> {
    await this.http.request("DELETE", `assets/folders/${pathId(folderId, "folderId")}/`, options);
  }
}

export interface AssetFileQuery extends ListQuery {
  /** Folder UUID; `root` for files outside any folder; `all` disables folder filtering. */
  folder_id?: string;
}

/** Media library files. */
export class AssetFilesResource extends BaseResource {
  /** `GET /api/v1/assets/files/` */
  list(query: AssetFileQuery = {}, options: RequestOptions = {}): Promise<Page<MediaAsset>> {
    return this.listPage<MediaAsset>("assets/files/", { ...query }, options);
  }

  /** `GET /api/v1/assets/files/{id}/` */
  async get(fileId: string, options: RequestOptions = {}): Promise<MediaAsset> {
    const res = await this.http.request<MediaAsset>("GET", `assets/files/${pathId(fileId, "fileId")}/`, options);
    return res.data;
  }

  /** `POST /api/v1/assets/files/upload/`: upload a file (a `Blob`/`File`, bytes, or `{ path }` in Node). */
  async upload(
    file: FileInput,
    params: FileUploadOptions & { folder?: string } = {},
    options: RequestOptions = {},
  ): Promise<MediaAsset> {
    const body = await buildUpload(file, { folder: params.folder }, params);
    const res = await this.http.request<MediaAsset>("POST", "assets/files/upload/", { ...options, body });
    return res.data;
  }

  /** `POST /api/v1/assets/files/`: upload a file with an explicit display name. */
  async create(
    file: FileInput,
    params: FileUploadOptions & { name: string; folder?: string },
    options: RequestOptions = {},
  ): Promise<MediaAsset> {
    const body = await buildUpload(file, { name: requireString(params.name, "name"), folder: params.folder }, params);
    const res = await this.http.request<MediaAsset>("POST", "assets/files/", { ...options, body });
    return res.data;
  }

  /** `PATCH /api/v1/assets/files/{id}/`: rename and/or move a file. */
  async update(
    fileId: string,
    params: { name?: string; folder?: string },
    options: RequestOptions = {},
  ): Promise<MediaAsset> {
    const body = new URLSearchParams();
    if (params.name !== undefined) body.set("name", requireString(params.name, "name"));
    if (params.folder !== undefined) body.set("folder", requireString(params.folder, "folder"));
    if (![...body.keys()].length) throw new NovaValidationError("Provide at least one of name or folder.");
    const res = await this.http.request<MediaAsset>("PATCH", `assets/files/${pathId(fileId, "fileId")}/`, { ...options, body });
    return res.data;
  }

  /** `DELETE /api/v1/assets/files/{id}/` */
  async delete(fileId: string, options: RequestOptions = {}): Promise<void> {
    await this.http.request("DELETE", `assets/files/${pathId(fileId, "fileId")}/`, options);
  }
}

/** The media library (folders and files). */
export class AssetsResource extends BaseResource {
  readonly folders: AssetFoldersResource;
  readonly files: AssetFilesResource;

  constructor(http: HttpTransport) {
    super(http);
    this.folders = new AssetFoldersResource(http);
    this.files = new AssetFilesResource(http);
  }
}
