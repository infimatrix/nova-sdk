package com.infimatrix.nova;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * Pagination details reported by list endpoints.
 *
 * @param count total number of items
 * @param next URL of the next page, or {@code null} on the last page
 * @param previous URL of the previous page, or {@code null}
 * @param page current 1-based page number
 * @param totalPages total number of pages
 * @param pageSize items per page
 */
@JsonIgnoreProperties(ignoreUnknown = true)
public record Pagination(
        @JsonProperty("count") long count,
        @JsonProperty("next") String next,
        @JsonProperty("previous") String previous,
        @JsonProperty("page") int page,
        @JsonProperty("total_pages") int totalPages,
        @JsonProperty("page_size") int pageSize) {

    /** Pagination describing a single page of {@code size} items (used when the server returns a bare array). */
    public static Pagination single(int size) {
        return new Pagination(size, null, null, 1, 1, size == 0 ? 20 : size);
    }
}
