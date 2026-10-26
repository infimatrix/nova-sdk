package com.infimatrix.nova;

import java.util.ArrayList;
import java.util.Collection;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;

/**
 * Query parameters of a list or filter call.
 *
 * <pre>{@code
 * Query q = Query.builder().search("acme").pageSize(50).param("timezone", "UTC").build();
 * }</pre>
 *
 * <p>Values are rendered with {@link String#valueOf(Object)}, so {@code Instant} and {@code LocalDate} produce
 * ISO-8601. Instances are immutable.
 */
public final class Query {
    private static final Query EMPTY = new Query(new LinkedHashMap<>());

    private final Map<String, List<String>> params;

    private Query(Map<String, List<String>> params) {
        this.params = params;
    }

    /** A query without parameters. */
    public static Query empty() {
        return EMPTY;
    }

    /** Returns a new builder. */
    public static Builder builder() {
        return new Builder();
    }

    /** Returns the parameters in insertion order (values of repeated keys in order). */
    public Map<String, List<String>> params() {
        return params;
    }

    /** Returns a builder pre-filled with this query's parameters. */
    public Builder toBuilder() {
        Builder b = new Builder();
        params.forEach((k, v) -> b.params.put(k, new ArrayList<>(v)));
        return b;
    }

    /** Builder for {@link Query}. */
    public static final class Builder {
        private final Map<String, List<String>> params = new LinkedHashMap<>();

        private Builder() {
        }

        /** Free-text search ({@code search}). */
        public Builder search(String value) {
            return param("search", value);
        }

        /** Sort field ({@code ordering}), for example {@code -created_at}. */
        public Builder ordering(String value) {
            return param("ordering", value);
        }

        /** 1-based page number ({@code page}). */
        public Builder page(int value) {
            return param("page", value);
        }

        /** Items per page ({@code page_size}). */
        public Builder pageSize(int value) {
            return param("page_size", value);
        }

        /** Sets (replaces) a parameter; {@code null} values are ignored; collections repeat the key. */
        public Builder param(String name, Object value) {
            Objects.requireNonNull(name, "name");
            if (value == null) {
                return this;
            }
            List<String> values = new ArrayList<>();
            if (value instanceof Collection<?> c) {
                c.forEach(v -> values.add(String.valueOf(v)));
            } else {
                values.add(String.valueOf(value));
            }
            params.put(name, values);
            return this;
        }

        /** Builds the immutable query. */
        public Query build() {
            Map<String, List<String>> copy = new LinkedHashMap<>();
            params.forEach((k, v) -> copy.put(k, List.copyOf(v)));
            return new Query(copy);
        }
    }
}
