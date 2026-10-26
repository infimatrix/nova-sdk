package com.infimatrix.nova;

import com.infimatrix.nova.errors.NovaClientValidationException;
import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Locale;
import java.util.Map;

/**
 * A file to upload as a multipart part. Content is held in memory.
 *
 * <pre>{@code
 * FileUpload.of(Path.of("logo.png"));
 * FileUpload.of(bytes, "logo.png");
 * }</pre>
 */
public final class FileUpload {
    private static final Map<String, String> MIME = Map.ofEntries(
            Map.entry(".csv", "text/csv"), Map.entry(".gif", "image/gif"), Map.entry(".htm", "text/html"),
            Map.entry(".html", "text/html"), Map.entry(".jpeg", "image/jpeg"), Map.entry(".jpg", "image/jpeg"),
            Map.entry(".json", "application/json"), Map.entry(".pdf", "application/pdf"),
            Map.entry(".png", "image/png"), Map.entry(".svg", "image/svg+xml"), Map.entry(".txt", "text/plain"),
            Map.entry(".webp", "image/webp"), Map.entry(".zip", "application/zip"));

    private final byte[] content;
    private final String filename;
    private final String contentType;

    private FileUpload(byte[] content, String filename, String contentType) {
        if (content == null || content.length == 0) {
            throw new NovaClientValidationException("file content is empty.");
        }
        if (filename == null || filename.isBlank()) {
            throw new NovaClientValidationException("filename is required when uploading raw bytes.");
        }
        this.content = content.clone();
        this.filename = filename;
        this.contentType = contentType != null ? contentType : guess(filename);
    }

    /** Uploads raw bytes under {@code filename}; the MIME type is guessed from the extension. */
    public static FileUpload of(byte[] content, String filename) {
        return new FileUpload(content, filename, null);
    }

    /** Uploads raw bytes with an explicit MIME type. */
    public static FileUpload of(byte[] content, String filename, String contentType) {
        return new FileUpload(content, filename, contentType);
    }

    /** Reads {@code path} fully; the filename is the file's name. */
    public static FileUpload of(Path path) {
        try {
            return new FileUpload(Files.readAllBytes(path), path.getFileName().toString(), null);
        } catch (IOException e) {
            throw new NovaClientValidationException("file path cannot be read: " + path);
        }
    }

    /** Reads {@code stream} fully from its current position (the caller closes it). */
    public static FileUpload of(InputStream stream, String filename) {
        try {
            return new FileUpload(stream.readAllBytes(), filename, null);
        } catch (IOException e) {
            throw new NovaClientValidationException("file stream cannot be read: " + e.getMessage());
        }
    }

    private static String guess(String filename) {
        int dot = filename.lastIndexOf('.');
        String ext = dot >= 0 ? filename.substring(dot).toLowerCase(Locale.ROOT) : "";
        return MIME.getOrDefault(ext, "application/octet-stream");
    }

    /** Returns a copy of the content. */
    public byte[] content() {
        return content.clone();
    }

    /** Filename sent to the server. */
    public String filename() {
        return filename;
    }

    /** MIME type sent to the server. */
    public String contentType() {
        return contentType;
    }

    /** Returns a copy with another MIME type. */
    public FileUpload withContentType(String type) {
        return new FileUpload(content, filename, type);
    }

    /** Returns a copy with another filename. */
    public FileUpload withFilename(String name) {
        return new FileUpload(content, name, contentType);
    }
}
