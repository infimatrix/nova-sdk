import { NovaValidationError } from "./errors.js";

/**
 * A file accepted by upload endpoints:
 * a `Blob`/`File`, raw bytes, or `{ path }` (Node.js only; read from disk).
 */
export type FileInput = Blob | Uint8Array | ArrayBuffer | { path: string };

export interface FileUploadOptions {
  /** Filename sent to the server. Required for raw bytes; inferred from `File.name` or `{ path }`. */
  filename?: string;
  /** MIME type. Guessed from the filename extension when omitted. */
  contentType?: string;
}

const MIME_BY_EXTENSION: Record<string, string> = {
  ".csv": "text/csv",
  ".gif": "image/gif",
  ".htm": "text/html",
  ".html": "text/html",
  ".jpeg": "image/jpeg",
  ".jpg": "image/jpeg",
  ".json": "application/json",
  ".pdf": "application/pdf",
  ".png": "image/png",
  ".svg": "image/svg+xml",
  ".txt": "text/plain",
  ".webp": "image/webp",
  ".zip": "application/zip",
};

function guessMime(filename: string): string {
  const dot = filename.lastIndexOf(".");
  return (dot >= 0 && MIME_BY_EXTENSION[filename.slice(dot).toLowerCase()]) || "application/octet-stream";
}

/** Normalise a {@link FileInput} to a `Blob` plus the filename to send. */
export async function resolveFile(
  file: FileInput,
  options: FileUploadOptions = {},
): Promise<{ blob: Blob; filename: string }> {
  let filename = options.filename;
  let content: Blob | Uint8Array | ArrayBuffer;

  if (typeof file === "object" && file !== null && "path" in file && typeof file.path === "string") {
    let readFile: (path: string) => Promise<Uint8Array>;
    try {
      const fs = await import("node:fs/promises");
      readFile = (path) => fs.readFile(path);
    } catch {
      throw new NovaValidationError("Reading files from a path requires Node.js.");
    }
    try {
      content = await readFile(file.path);
    } catch {
      throw new NovaValidationError(`file path does not exist: ${file.path}`);
    }
    filename ??= file.path.split(/[\\/]/).pop();
  } else if (file instanceof Blob || file instanceof Uint8Array || file instanceof ArrayBuffer) {
    content = file;
    if (!filename && file instanceof Blob && "name" in file && typeof file.name === "string") filename = file.name;
  } else {
    throw new NovaValidationError("file must be a Blob, Uint8Array, ArrayBuffer, or { path }.");
  }

  const size = content instanceof Blob ? content.size : content.byteLength;
  if (size === 0) throw new NovaValidationError("file content is empty.");
  if (!filename) throw new NovaValidationError("filename is required when uploading raw bytes.");

  const type = options.contentType ?? (content instanceof Blob && content.type ? content.type : guessMime(filename));
  const blob = content instanceof Blob ? content.slice(0, content.size, type) : new Blob([content as Uint8Array<ArrayBuffer>], { type });
  return { blob, filename };
}

/** Build multipart form data with one file part named `file` plus string fields. */
export async function buildUpload(
  file: FileInput,
  fields: Record<string, string | undefined>,
  options: FileUploadOptions = {},
): Promise<FormData> {
  const { blob, filename } = await resolveFile(file, options);
  const form = new FormData();
  for (const [key, value] of Object.entries(fields)) if (value !== undefined) form.append(key, value);
  form.append("file", blob, filename);
  return form;
}
