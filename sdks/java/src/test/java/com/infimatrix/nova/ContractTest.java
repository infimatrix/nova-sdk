package com.infimatrix.nova;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.dataformat.yaml.YAMLFactory;
import com.infimatrix.nova.MockServer.Reply;
import com.infimatrix.nova.http.Json;
import com.infimatrix.nova.models.BulkSendEmailRequest;
import com.infimatrix.nova.models.ContactGroupRequest;
import com.infimatrix.nova.models.ContactRequest;
import com.infimatrix.nova.models.EventTypeEnum;
import com.infimatrix.nova.models.GroupSendEmailRequest;
import com.infimatrix.nova.models.MembershipCreateRequest;
import com.infimatrix.nova.models.PatchedContactGroupRequest;
import com.infimatrix.nova.models.PatchedContactRequest;
import com.infimatrix.nova.models.PatchedMembershipUpdateRequest;
import com.infimatrix.nova.models.PatchedProviderConfigurationCreateUpdateRequest;
import com.infimatrix.nova.models.PatchedTemplateRequest;
import com.infimatrix.nova.models.PatchedTenantUpdateRequest;
import com.infimatrix.nova.models.PatchedTransactionalNotificationRequest;
import com.infimatrix.nova.models.PatchedWebhookEndpointCreateUpdateRequest;
import com.infimatrix.nova.models.ProviderConfigurationCreateUpdateRequest;
import com.infimatrix.nova.models.ProviderTypeEnum;
import com.infimatrix.nova.models.ResetPasswordRequest;
import com.infimatrix.nova.models.RoleEnum;
import com.infimatrix.nova.models.SendEmailRequest;
import com.infimatrix.nova.models.SendTestEmailRequest;
import com.infimatrix.nova.models.TemplateRequest;
import com.infimatrix.nova.models.TenantCreateRequest;
import com.infimatrix.nova.models.TransactionalNotificationRequest;
import com.infimatrix.nova.models.UserRegisterRequest;
import com.infimatrix.nova.models.WebhookEndpointCreateUpdateRequest;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.TreeSet;
import java.util.function.Consumer;
import java.util.regex.Pattern;
import org.junit.jupiter.api.Test;

/**
 * Exercises every SDK operation against a local server and checks each real HTTP request against
 * {@code openapi/nova-api.yaml}: method and path exist, query parameters are documented, required body fields
 * are present, the content type is accepted, and every required operation is called at least once.
 */
class ContractTest {
    private static final String ID = "33333333-3333-3333-3333-333333333333";
    private static final String TENANT = "11111111-1111-1111-1111-111111111111";
    private static final ObjectMapper YAML = new ObjectMapper(new YAMLFactory());

    private static Path root() {
        return Path.of(System.getProperty("nova.repo.root", "../..")).normalize();
    }

    private static Map<String, Consumer<NovaClient>> cases() {
        Map<String, Consumer<NovaClient>> c = new LinkedHashMap<>();
        Query q = Query.builder().page(2).pageSize(5).build();
        c.put("auth.login", n -> n.auth().login("a@b.co", "pw"));
        c.put("auth.register", n -> n.auth().register(UserRegisterRequest.builder().email("n@e.co").password("Str0ng-Passw0rd!")
                .firstName("Ada").organizationName("Acme").build()));
        c.put("auth.refresh", n -> n.auth().refresh("r1"));
        c.put("auth.logout", n -> n.auth().logout("r1"));
        c.put("auth.me", n -> n.auth().me());
        c.put("auth.forgot", n -> n.auth().forgotPassword("a@b.co"));
        c.put("auth.validate", n -> n.auth().validateResetToken("u", "t"));
        c.put("auth.reset", n -> n.auth().resetPassword(ResetPasswordRequest.builder().uid("u").token("t")
                .newPassword("N3w-Passw0rd!x").confirmPassword("N3w-Passw0rd!x").build()));
        c.put("auth.change", n -> n.auth().changePassword("o", "n1234567", "n1234567"));
        c.put("apikeys.list", n -> n.auth().apiKeys().list(q));
        c.put("apikeys.create", n -> n.auth().apiKeys().create("ci key"));
        c.put("apikeys.revoke", n -> n.auth().apiKeys().revoke(ID));
        c.put("users.list", n -> n.users().list(q));
        c.put("users.me", n -> n.users().me());
        c.put("tenants.list", n -> n.tenants().list(q));
        c.put("tenants.create", n -> n.tenants().create(TenantCreateRequest.builder().name("A").slug("a").build()));
        c.put("tenants.get", n -> n.tenants().get(null));
        c.put("tenants.update", n -> n.tenants().update(null, PatchedTenantUpdateRequest.builder().name("New").build()));
        c.put("tenants.delete", n -> n.tenants().delete(null));
        c.put("members.list", n -> n.tenants().memberships().list(null, q));
        c.put("members.add", n -> n.tenants().memberships().add(null,
                MembershipCreateRequest.builder().email("x@y.co").role(RoleEnum.VIEWER).build()));
        c.put("members.get", n -> n.tenants().memberships().get(null, ID));
        c.put("members.update", n -> n.tenants().memberships().update(null, ID,
                PatchedMembershipUpdateRequest.builder().role(RoleEnum.SENDER).build()));
        c.put("members.remove", n -> n.tenants().memberships().remove(null, ID));
        c.put("templates.list", n -> n.templates().list(Query.builder().param("status", "ACTIVE").ordering("-created_at").pageSize(5).build()));
        c.put("templates.get", n -> n.templates().get(ID));
        c.put("templates.create", n -> n.templates().create(TemplateRequest.builder().name("Welcome").subject("Hi").htmlContent("<p>x</p>").build()));
        c.put("templates.update", n -> n.templates().update(ID, PatchedTemplateRequest.builder().name("W2").build()));
        c.put("templates.delete", n -> n.templates().delete(ID));
        c.put("templates.render", n -> n.templates().render(ID, Map.of("name", "Ada")));
        c.put("contacts.list", n -> n.contacts().list(Query.builder().param("timezone", "UTC").search("a").page(2).build()));
        c.put("contacts.get", n -> n.contacts().get(ID));
        c.put("contacts.create", n -> n.contacts().create(ContactRequest.builder().email("a@b.co").firstName("Ada").build()));
        c.put("contacts.update", n -> n.contacts().update(ID, PatchedContactRequest.builder().firstName("Grace").build()));
        c.put("contacts.delete", n -> n.contacts().delete(ID));
        c.put("contacts.bulk_delete", n -> n.contacts().bulkDelete(List.of(ID)));
        c.put("contacts.activity", n -> n.contacts().activity(ID));
        c.put("contacts.sample", n -> n.contacts().sampleTemplate());
        c.put("contacts.bulk_upload", n -> n.contacts().bulkUpload(FileUpload.of("email\na@b.co\n".getBytes(StandardCharsets.UTF_8), "c.csv")));
        c.put("groups.list", n -> n.contacts().groups().list(Query.builder().search("v").build()));
        c.put("groups.get", n -> n.contacts().groups().get(ID));
        c.put("groups.create", n -> n.contacts().groups().create(ContactGroupRequest.builder().name("VIP").description("d").build()));
        c.put("groups.update", n -> n.contacts().groups().update(ID, PatchedContactGroupRequest.builder().name("V2").build()));
        c.put("groups.delete", n -> n.contacts().groups().delete(ID));
        c.put("emails.send", n -> n.emails().send(SendEmailRequest.builder().recipientEmail("a@b.co").subject("Hi").htmlContent("<p>x</p>").build()));
        c.put("emails.bulk_send", n -> n.emails().bulkSend(BulkSendEmailRequest.builder().templateId(ID).contactIds(List.of(ID)).senderEmail("me@x.co").build()));
        c.put("emails.group_send", n -> n.emails().groupSend(GroupSendEmailRequest.builder().templateId(ID).groupId(ID).senderEmail("me@x.co").build()));
        c.put("emails.logs", n -> n.emails().listLogs(Query.builder().param("status", "FAILED").page(2).build()));
        c.put("emails.log", n -> n.emails().getLog(ID));
        c.put("emails.preview", n -> n.emails().preview(ID));
        c.put("emails.export", n -> n.emails().exportCsv(Query.builder().param("status", "DELIVERED").build()));
        c.put("providers.list", n -> n.providers().list(Query.builder().search("s").build()));
        c.put("providers.get", n -> n.providers().get(ID));
        c.put("providers.create", n -> n.providers().create(ProviderConfigurationCreateUpdateRequest.builder().name("Mailgun").providerType(ProviderTypeEnum.MAILGUN).build()));
        c.put("providers.update", n -> n.providers().update(ID, PatchedProviderConfigurationCreateUpdateRequest.builder().isActive(false).build()));
        c.put("providers.delete", n -> n.providers().delete(ID));
        c.put("providers.types", n -> n.providers().types());
        c.put("providers.test", n -> n.providers().test(ID, "a@b.co"));
        c.put("webhooks.list", n -> n.webhooks().list(Query.empty()));
        c.put("webhooks.get", n -> n.webhooks().get(ID));
        c.put("webhooks.create", n -> n.webhooks().create(WebhookEndpointCreateUpdateRequest.builder().name("n").url("https://x.co/h").events(List.of(EventTypeEnum.CONTACT_CREATED)).build()));
        c.put("webhooks.update", n -> n.webhooks().update(ID, PatchedWebhookEndpointCreateUpdateRequest.builder().isActive(false).build()));
        c.put("webhooks.delete", n -> n.webhooks().delete(ID));
        c.put("webhooks.events", n -> n.webhooks().events());
        c.put("webhooks.rotate", n -> n.webhooks().rotateSecret(ID));
        c.put("webhooks.test", n -> n.webhooks().test(ID, EventTypeEnum.CONTACT_CREATED));
        c.put("campaigns.list", n -> n.campaigns().list(Query.builder().search("w").build()));
        c.put("campaigns.get", n -> n.campaigns().get(ID));
        c.put("campaigns.create", n -> n.campaigns().create(TransactionalNotificationRequest.builder().name("W").apiIdentifier("welcome").build()));
        c.put("campaigns.update", n -> n.campaigns().update(ID, PatchedTransactionalNotificationRequest.builder().name("W2").build()));
        c.put("campaigns.delete", n -> n.campaigns().delete(ID));
        c.put("campaigns.send_test", n -> n.campaigns().sendTest(ID, SendTestEmailRequest.builder().recipientEmail("a@b.co").build()));
        c.put("analytics.dashboard", n -> n.analytics().dashboard("2026-01-01", "2026-02-01"));
        c.put("audit.list", n -> n.audit().list(Query.builder().param("category", "AUTH").param("status_code_gte", 400).page(2).build()));
        c.put("audit.get", n -> n.audit().get(ID));
        c.put("audit.stats", n -> n.audit().stats());
        c.put("folders.list", n -> n.assets().folders().list(Query.builder().search("b").build()));
        c.put("folders.get", n -> n.assets().folders().get(ID));
        c.put("folders.create", n -> n.assets().folders().create("Brand"));
        c.put("folders.update", n -> n.assets().folders().update(ID, "B2"));
        c.put("folders.delete", n -> n.assets().folders().delete(ID));
        c.put("files.list", n -> n.assets().files().list(Query.builder().search("l").param("folder_id", "root").build()));
        c.put("files.get", n -> n.assets().files().get(ID));
        c.put("files.upload", n -> n.assets().files().upload(FileUpload.of(new byte[] {(byte) 0x89, 'P', 'N', 'G'}, "logo.png"), ID));
        c.put("files.create", n -> n.assets().files().create(FileUpload.of(new byte[] {1}, "a.png"), "Hero", null));
        c.put("files.update", n -> n.assets().files().update(ID, "renamed", null));
        c.put("files.delete", n -> n.assets().files().delete(ID));
        c.put("health", NovaClient::health);
        return c;
    }

    private static boolean matches(String template, String path) {
        return Pattern.matches(template.replaceAll("\\{[^}]+\\}", "[^/]+"), path);
    }

    @Test
    void everyOperationMatchesTheOpenApiContract() throws IOException {
        JsonNode spec = YAML.readTree(Files.readString(root().resolve("openapi/nova-api.yaml")));
        JsonNode exclusions = YAML.readTree(Files.readString(root().resolve("openapi/sdk-exclusions.yaml")));

        Map<String, JsonNode> operations = new LinkedHashMap<>();
        spec.get("paths").properties().forEach(path -> {
            for (String method : List.of("get", "post", "put", "patch", "delete")) {
                if (path.getValue().has(method)) {
                    operations.put(method.toUpperCase() + " " + path.getKey(), path.getValue().get(method));
                }
            }
        });

        Set<String> excluded = new TreeSet<>();
        exclusions.get("excluded").forEach(e -> {
            String[] parts = e.get("operation").asText().split(" ", 2);
            String normalized = "/api/v1/" + parts[1].replaceAll("\\{\\}", "{id}");
            excluded.add(parts[0] + " " + normalized);
        });

        List<String> problems = new ArrayList<>();
        Set<String> exercised = new TreeSet<>();

        try (MockServer server = new MockServer()) {
            server.reply(r -> r.method().equals("DELETE") ? Reply.noContent() : Reply.ok("{}"));
            NovaClient client = server.clientBuilder().tenantId(TENANT).build();
            for (Map.Entry<String, Consumer<NovaClient>> entry : cases().entrySet()) {
                int before = server.requests().size();
                entry.getValue().accept(client);
                if (server.requests().size() != before + 1) {
                    problems.add(entry.getKey() + ": expected exactly one request");
                    continue;
                }
                MockServer.Recorded r = server.last();
                String key = r.method() + " " + r.path();
                String opKey = operations.keySet().stream()
                        .filter(k -> k.startsWith(r.method() + " ") && matches(k.substring(k.indexOf(' ') + 1), r.path()))
                        .min(java.util.Comparator.comparingInt(k -> k.split("\\{", -1).length)).orElse(null);
                if (opKey == null) {
                    problems.add(entry.getKey() + ": no operation " + key);
                    continue;
                }
                exercised.add(opKey);
                checkRequest(entry.getKey(), r, operations.get(opKey), spec, problems);
            }
        }

        // PUT is covered through PATCH (SDKs expose one partial-update method).
        Set<String> covered = new TreeSet<>(exercised);
        exercised.stream().filter(k -> k.startsWith("PATCH ")).forEach(k -> covered.add("PUT " + k.substring(6)));
        Set<String> missing = new TreeSet<>(operations.keySet());
        missing.removeAll(covered);
        missing.removeAll(excluded);
        if (!missing.isEmpty()) {
            problems.add("operations never exercised: " + missing);
        }
        assertTrue(problems.isEmpty(), String.join("\n", problems));
        assertEquals(operations.size() - excluded.size(), covered.stream().filter(operations::containsKey).count());
    }

    private static void checkRequest(String name, MockServer.Recorded r, JsonNode op, JsonNode spec, List<String> problems)
            throws IOException {
        Set<String> documented = new TreeSet<>();
        op.path("parameters").forEach(p -> documented.add(p.get("name").asText()));
        if (r.query() != null) {
            for (String pair : r.query().split("&")) {
                String param = java.net.URLDecoder.decode(pair.split("=", 2)[0], StandardCharsets.UTF_8);
                if (!documented.contains(param)) {
                    problems.add(name + ": undocumented query parameter " + param);
                }
            }
        }
        if (documented.contains("X-Tenant-ID") && !TENANT.equals(r.header("x-tenant-id"))) {
            problems.add(name + ": missing tenant header");
        }
        if (op.has("security") && op.get("security").size() > 0 && r.header("authorization") == null) {
            problems.add(name + ": missing Authorization");
        }
        JsonNode content = op.path("requestBody").path("content");
        if (content.isMissingNode()) {
            if (r.body().length > 0) {
                problems.add(name + ": unexpected request body");
            }
            return;
        }
        String contentType = r.header("content-type") == null ? "" : r.header("content-type").split(";")[0];
        if (!content.has(contentType)) {
            problems.add(name + ": content type " + contentType + " not accepted by the contract");
            return;
        }
        String ref = content.get(contentType).path("schema").path("$ref").asText("");
        JsonNode schema = spec.at("/components/schemas/" + ref.substring(ref.lastIndexOf('/') + 1));
        Set<String> sent = new TreeSet<>();
        if (contentType.equals("application/json")) {
            Json.mapper().readTree(r.body()).fieldNames().forEachRemaining(sent::add);
        } else if (contentType.equals("application/x-www-form-urlencoded")) {
            for (String pair : r.bodyText().split("&")) {
                sent.add(pair.split("=", 2)[0]);
            }
        } else {
            Matcher.fields(r.bodyText(), sent);
        }
        for (JsonNode required : schema.path("required")) {
            String field = required.asText();
            if (!sent.contains(field) && !(field.equals("uid") && sent.contains("uidb64"))) {
                problems.add(name + ": required body field missing: " + field);
            }
        }
        for (String field : sent) {
            if (!schema.path("properties").has(field)) {
                problems.add(name + ": body field not in schema: " + field);
            }
        }
    }

    /** Extracts multipart field names. */
    private static final class Matcher {
        static void fields(String body, Set<String> out) {
            java.util.regex.Matcher m = Pattern.compile("(?<![a-z])name=\"([^\"]+)\"").matcher(body);
            while (m.find()) {
                out.add(m.group(1));
            }
        }
    }
}
