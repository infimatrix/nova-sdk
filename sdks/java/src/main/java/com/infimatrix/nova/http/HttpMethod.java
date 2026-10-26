package com.infimatrix.nova.http;

/** HTTP methods used by the Nova API. */
public enum HttpMethod {
    /** HTTP GET (idempotent; retried automatically). */
    GET,
    /** HTTP POST (never retried automatically). */
    POST,
    /** HTTP PUT (never retried automatically). */
    PUT,
    /** HTTP PATCH (never retried automatically). */
    PATCH,
    /** HTTP DELETE (never retried automatically). */
    DELETE;

    /** Whether the method is safe to retry automatically. */
    public boolean idempotent() {
        return this == GET;
    }
}
