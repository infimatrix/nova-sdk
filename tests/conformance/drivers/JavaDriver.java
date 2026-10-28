import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.infimatrix.nova.NovaClient;
import com.infimatrix.nova.Page;
import com.infimatrix.nova.Query;
import com.infimatrix.nova.errors.*;
import com.infimatrix.nova.models.Template;
import com.infimatrix.nova.models.TemplateRequest;
import java.time.Duration;
import java.util.ArrayList;
import java.util.List;
import java.util.TreeSet;

/** Conformance driver for the Java SDK: performs one abstract call and prints a normalised outcome. */
public final class JavaDriver {
    static final ObjectMapper M = new ObjectMapper();

    static String categorise(Throwable e) {
        if (e instanceof NovaRedirectException) return "Redirect";
        if (e instanceof NovaRateLimitException) return "RateLimit";
        if (e instanceof NovaAuthenticationException) return "Authentication";
        if (e instanceof NovaPermissionException) return "Permission";
        if (e instanceof NovaNotFoundException) return "NotFound";
        if (e instanceof NovaValidationException || e instanceof NovaClientValidationException) return "Validation";
        if (e instanceof NovaServerException) return "Server";
        if (e instanceof NovaApiException) return "API";
        if (e instanceof NovaTimeoutException) return "Timeout";
        if (e instanceof NovaConnectionException) return "Connection";
        return "Other:" + e.getClass().getSimpleName();
    }

    public static void main(String[] args) throws Exception {
        JsonNode spec = M.readTree(args[0]);
        JsonNode c = spec.get("client");
        JsonNode call = spec.get("call");
        NovaClient.Builder b = NovaClient.builder().baseUrl(spec.get("base_url").asText())
                .retryBackoff(Duration.ofMillis(c.has("retry_backoff_ms") ? c.get("retry_backoff_ms").asLong() : 1)).retryJitter(false);
        if (c.has("api_key")) b.apiKey(c.get("api_key").asText());
        if (c.has("access_token")) b.accessToken(c.get("access_token").asText());
        if (c.has("tenant_id")) b.tenantId(c.get("tenant_id").asText());
        if (c.has("max_retries")) b.maxRetries(c.get("max_retries").asInt());
        if (c.has("timeout_ms")) b.requestTimeout(Duration.ofMillis(c.get("timeout_ms").asLong()));
        ObjectNode out = M.createObjectNode();
        try {
            NovaClient nova = b.build();
            if (call.has("tenant_id")) nova = nova.withTenant(call.get("tenant_id").asText());
            String op = call.get("op").asText();
            Object data = null;
            switch (op) {
                case "health" -> data = nova.health();
                case "templates.get" -> {
                    Template t = nova.templates().get(call.get("id").asText());
                    data = java.util.Map.of("id", t.id(), "name", t.name());
                }
                case "templates.delete" -> nova.templates().delete(call.get("id").asText());
                case "templates.create" -> {
                    TemplateRequest.Builder tb = TemplateRequest.builder().name(call.get("name").asText());
                    if (call.has("subject")) tb.subject(call.get("subject").asText());
                    nova.templates().create(tb.build());
                }
                case "templates.list" -> {
                    Query.Builder qb = Query.builder();
                    if (call.has("page")) qb.page(call.get("page").asInt());
                    if (call.has("page_size")) qb.pageSize(call.get("page_size").asInt());
                    if (call.has("search")) qb.search(call.get("search").asText());
                    Page<Template> page = nova.templates().list(qb.build());
                    List<String> ids = new ArrayList<>();
                    for (Template t : page.items()) ids.add(t.id());
                    data = java.util.Map.of("ids", ids, "has_next", page.hasNext());
                }
                case "templates.iter_all" -> {
                    Page<Template> page = nova.templates().list(Query.builder().pageSize(call.get("page_size").asInt()).build());
                    List<String> ids = new ArrayList<>();
                    for (Template t : page) ids.add(t.id());
                    data = java.util.Map.of("ids", ids);
                }
                default -> throw new IllegalArgumentException("unknown op " + op);
            }
            out.put("kind", "ok");
            out.set("data", M.valueToTree(data));
        } catch (NovaException e) {
            out.put("kind", "error");
            out.put("category", categorise(e));
            out.set("status", e.statusCode() == null || e.statusCode() == 0 ? M.nullNode() : M.valueToTree(e.statusCode()));
            out.put("code", e.errorCode());
            out.put("correlation_id", e.correlationId());
            if (e instanceof NovaRateLimitException r && r.retryAfter() != null) {
                Object ra = r.retryAfter();
                out.set("retry_after", ra instanceof Duration d ? M.valueToTree(d.toSeconds()) : M.valueToTree(ra));
            } else {
                out.set("retry_after", M.nullNode());
            }
            TreeSet<String> keys = new TreeSet<>();
            Object details = e.details();
            if (details != null) {
                JsonNode dn = M.valueToTree(details);
                if (dn.isObject()) dn.fieldNames().forEachRemaining(keys::add);
            }
            out.set("details_keys", M.valueToTree(keys));
            out.put("message", e.getMessage() + " | " + e);
        }
        System.out.println(M.writeValueAsString(out));
    }
}
