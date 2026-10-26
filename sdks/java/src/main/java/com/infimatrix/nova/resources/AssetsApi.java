package com.infimatrix.nova.resources;

import com.infimatrix.nova.FileUpload;
import com.infimatrix.nova.Page;
import com.infimatrix.nova.Query;
import com.infimatrix.nova.errors.NovaClientValidationException;
import com.infimatrix.nova.http.ApiRequest;
import com.infimatrix.nova.http.HttpMethod;
import com.infimatrix.nova.http.HttpTransport;
import com.infimatrix.nova.models.AssetFolder;
import com.infimatrix.nova.models.AssetFolderRequest;
import com.infimatrix.nova.models.MediaAsset;
import com.infimatrix.nova.models.PatchedAssetFolderRequest;
import java.util.LinkedHashMap;
import java.util.Map;

/** The media library (folders and files). */
public final class AssetsApi {
    private final FoldersApi folders;
    private final FilesApi files;

    /** Creates the API; use {@code NovaClient#assets()}. */
    public AssetsApi(HttpTransport http) {
        this.folders = new FoldersApi(http);
        this.files = new FilesApi(http);
    }

    /** Media library folders. */
    public FoldersApi folders() {
        return folders;
    }

    /** Media library files. */
    public FilesApi files() {
        return files;
    }

    /** Media library folders. */
    public static final class FoldersApi {
        private final HttpTransport http;

        FoldersApi(HttpTransport http) {
            this.http = http;
        }

        /** {@code GET /api/v1/assets/folders/}. */
        public Page<AssetFolder> list(Query query) {
            return http.listPage("assets/folders/", query, AssetFolder.class);
        }

        /** {@code GET /api/v1/assets/folders/{id}/}. */
        public AssetFolder get(String folderId) {
            return http.send(ApiRequest.of(HttpMethod.GET, "assets/folders/{}/", Validate.nonBlank(folderId, "folderId")),
                    AssetFolder.class);
        }

        /** {@code POST /api/v1/assets/folders/}. */
        public AssetFolder create(String name) {
            return http.send(ApiRequest.of(HttpMethod.POST, "assets/folders/")
                    .json(AssetFolderRequest.builder().name(Validate.nonBlank(name, "name")).build()), AssetFolder.class);
        }

        /** {@code PATCH /api/v1/assets/folders/{id}/}: renames a folder. */
        public AssetFolder update(String folderId, String name) {
            return http.send(ApiRequest.of(HttpMethod.PATCH, "assets/folders/{}/", Validate.nonBlank(folderId, "folderId"))
                    .json(PatchedAssetFolderRequest.builder().name(Validate.nonBlank(name, "name")).build()),
                    AssetFolder.class);
        }

        /** {@code DELETE /api/v1/assets/folders/{id}/}. */
        public void delete(String folderId) {
            http.send(ApiRequest.of(HttpMethod.DELETE, "assets/folders/{}/", Validate.nonBlank(folderId, "folderId")));
        }
    }

    /** Media library files. */
    public static final class FilesApi {
        private final HttpTransport http;

        FilesApi(HttpTransport http) {
            this.http = http;
        }

        /** {@code GET /api/v1/assets/files/}; restrict with {@code Query.builder().param("folder_id", "root")}. */
        public Page<MediaAsset> list(Query query) {
            return http.listPage("assets/files/", query, MediaAsset.class);
        }

        /** {@code GET /api/v1/assets/files/{id}/}. */
        public MediaAsset get(String fileId) {
            return http.send(ApiRequest.of(HttpMethod.GET, "assets/files/{}/", Validate.nonBlank(fileId, "fileId")),
                    MediaAsset.class);
        }

        /** {@code POST /api/v1/assets/files/upload/}; {@code folderId} may be null. */
        public MediaAsset upload(FileUpload file, String folderId) {
            Map<String, String> fields = new LinkedHashMap<>();
            if (folderId != null) {
                fields.put("folder", Validate.nonBlank(folderId, "folder"));
            }
            return http.send(ApiRequest.of(HttpMethod.POST, "assets/files/upload/").multipart(fields, file), MediaAsset.class);
        }

        /** {@code POST /api/v1/assets/files/}: uploads with an explicit display name; {@code folderId} may be null. */
        public MediaAsset create(FileUpload file, String name, String folderId) {
            Map<String, String> fields = new LinkedHashMap<>();
            fields.put("name", Validate.nonBlank(name, "name"));
            if (folderId != null) {
                fields.put("folder", Validate.nonBlank(folderId, "folder"));
            }
            return http.send(ApiRequest.of(HttpMethod.POST, "assets/files/").multipart(fields, file), MediaAsset.class);
        }

        /** {@code PATCH /api/v1/assets/files/{id}/}: renames and/or moves a file (either argument may be null). */
        public MediaAsset update(String fileId, String name, String folderId) {
            Map<String, String> fields = new LinkedHashMap<>();
            if (name != null) {
                fields.put("name", Validate.nonBlank(name, "name"));
            }
            if (folderId != null) {
                fields.put("folder", Validate.nonBlank(folderId, "folder"));
            }
            if (fields.isEmpty()) {
                throw new NovaClientValidationException("Provide at least one of name or folder.");
            }
            return http.send(ApiRequest.of(HttpMethod.PATCH, "assets/files/{}/", Validate.nonBlank(fileId, "fileId"))
                    .form(fields), MediaAsset.class);
        }

        /** {@code DELETE /api/v1/assets/files/{id}/}. */
        public void delete(String fileId) {
            http.send(ApiRequest.of(HttpMethod.DELETE, "assets/files/{}/", Validate.nonBlank(fileId, "fileId")));
        }
    }
}
