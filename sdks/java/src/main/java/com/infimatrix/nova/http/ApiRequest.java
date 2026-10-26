package com.infimatrix.nova.http;

import com.infimatrix.nova.FileUpload;
import com.infimatrix.nova.Query;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;

/**
 * Description of one API call, independent of the HTTP client.
 *
 * <p>The path is a template relative to {@code /api/v1/} whose {@code {}} placeholders are filled, in order,
 * with URL-encoded arguments, for example {@code ApiRequest.of(HttpMethod.GET, "tenants/{}/members/{}/", t, m)}.
 */
public final class ApiRequest {
    private final HttpMethod method;
    private final String template;
    private final List<String> pathArgs;
    private Query query = Query.empty();
    private Object json;
    private Map<String, String> formFields;
    private FileUpload file;
    private boolean multipart;
    private Boolean allowRetry;

    private ApiRequest(HttpMethod method, String template, List<String> pathArgs) {
        this.method = method;
        this.template = template;
        this.pathArgs = pathArgs;
    }

    /** Creates a request for {@code template}, substituting {@code pathArgs} for the {@code {}} placeholders. */
    public static ApiRequest of(HttpMethod method, String template, Object... pathArgs) {
        List<String> args = new ArrayList<>();
        for (Object arg : pathArgs) {
            args.add(String.valueOf(arg));
        }
        return new ApiRequest(Objects.requireNonNull(method), Objects.requireNonNull(template), args);
    }

    /** Sets the query string parameters. */
    public ApiRequest query(Query value) {
        this.query = value == null ? Query.empty() : value;
        return this;
    }

    /** Sets a JSON request body (serialized with the SDK's mapper). */
    public ApiRequest json(Object body) {
        this.json = body;
        return this;
    }

    /** Sends {@code application/x-www-form-urlencoded} fields. */
    public ApiRequest form(Map<String, String> fields) {
        this.formFields = new LinkedHashMap<>(fields);
        return this;
    }

    /** Sends {@code multipart/form-data} with text {@code fields} and one {@code file} part. */
    public ApiRequest multipart(Map<String, String> fields, FileUpload upload) {
        this.formFields = new LinkedHashMap<>(fields);
        this.file = upload;
        this.multipart = true;
        return this;
    }

    /** Forces (true) or forbids (false) automatic retries. Default: only GET is retried. */
    public ApiRequest allowRetry(boolean value) {
        this.allowRetry = value;
        return this;
    }

    /** HTTP method. */
    public HttpMethod method() {
        return method;
    }

    /** Path template. */
    public String template() {
        return template;
    }

    /** Raw (unencoded) path arguments. */
    public List<String> pathArgs() {
        return pathArgs;
    }

    /** Query parameters. */
    public Query query() {
        return query;
    }

    /** JSON body, or {@code null}. */
    public Object json() {
        return json;
    }

    /** Form or multipart text fields, or {@code null}. */
    public Map<String, String> formFields() {
        return formFields;
    }

    /** File part, or {@code null}. */
    public FileUpload file() {
        return file;
    }

    /** Whether the body is multipart. */
    public boolean isMultipart() {
        return multipart;
    }

    /** Retry override, or {@code null} for the default. */
    public Boolean allowRetry() {
        return allowRetry;
    }
}
