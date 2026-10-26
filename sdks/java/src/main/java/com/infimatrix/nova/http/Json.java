package com.infimatrix.nova.http;

import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;

/** The shared Jackson configuration. {@link ObjectMapper} is thread-safe once configured. */
public final class Json {
    private static final ObjectMapper MAPPER = new ObjectMapper()
            .configure(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, false)
            .configure(SerializationFeature.FAIL_ON_EMPTY_BEANS, false);

    private Json() {
    }

    /** Returns the shared mapper. Do not reconfigure it. */
    public static ObjectMapper mapper() {
        return MAPPER;
    }
}
