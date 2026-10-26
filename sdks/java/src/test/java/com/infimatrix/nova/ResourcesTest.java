package com.infimatrix.nova;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.infimatrix.nova.MockServer.Reply;
import com.infimatrix.nova.errors.NovaClientValidationException;
import com.infimatrix.nova.errors.NovaNotFoundException;
import com.infimatrix.nova.http.Json;
import com.infimatrix.nova.models.ContactRequest;
import com.infimatrix.nova.models.Login;
import com.infimatrix.nova.models.MediaAsset;
import com.infimatrix.nova.models.PatchedMembershipUpdateRequest;
import com.infimatrix.nova.models.PatchedTemplateRequest;
import com.infimatrix.nova.models.SendEmailRequest;
import com.infimatrix.nova.models.TenantCreateRequest;
import com.infimatrix.nova.models.TemplateStatusEnum;
import com.infimatrix.nova.models.UserRegisterRequest;
import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

class ResourcesTest {
    private static final String ID = "33333333-3333-3333-3333-333333333333";
    private static final String TENANT = "11111111-1111-1111-1111-111111111111";

    private static JsonNode json(MockServer.Recorded r) throws IOException {
        return Json.mapper().readTree(r.body());
    }

    @Test
    void loginPostsCredentialsAndReturnsTokens() throws IOException {
        try (MockServer server = new MockServer()) {
            server.reply(Reply.ok("{\"access\":\"jwt-1\",\"refresh\":\"r-1\",\"user\":{},\"tenants\":[]}"));
            NovaClient client = server.clientBuilder().build();
            Login login = client.auth().login(" a@b.co ", "pw");
            assertEquals("jwt-1", login.access());
            assertEquals("a@b.co", json(server.last()).get("email").asText());
            assertEquals("application/json", server.last().header("content-type"));

            NovaClient viaToken = NovaClient.builder().baseUrl(server.url()).build().withAccessToken(login.access());
            viaToken.auth().me();
            assertEquals("Bearer jwt-1", server.last().header("authorization"));
        }
    }

    @Test
    void clientSideValidationHappensBeforeAnyRequest() {
        try (MockServer server = new MockServer()) {
            NovaClient client = server.clientBuilder().build();
            assertThrows(NovaClientValidationException.class, () -> client.auth().login("", "pw"));
            assertThrows(NovaClientValidationException.class, () -> client.auth().login("a@b.co", ""));
            assertThrows(NovaClientValidationException.class, () -> client.auth().refresh(" "));
            assertThrows(NovaClientValidationException.class, () -> client.auth().forgotPassword(null));
            assertThrows(NovaClientValidationException.class, () -> client.contacts().bulkDelete(List.of()));
            assertThrows(NovaClientValidationException.class,
                    () -> client.emails().send(SendEmailRequest.builder().recipientEmail("").subject("s").build()));
            assertThrows(NovaClientValidationException.class,
                    () -> client.tenants().memberships().update(TENANT, ID, PatchedMembershipUpdateRequest.builder().build()));
            assertThrows(NovaClientValidationException.class, () -> client.assets().files().update(ID, null, null));
            assertThrows(NovaClientValidationException.class, () -> client.tenants().get(null));
            assertEquals(0, server.requests().size());
        }
    }

    @Test
    void requestBuildersOmitUnsetFieldsAndUseSnakeCase() throws IOException {
        TenantCreateRequest request = TenantCreateRequest.builder().name("A").slug("a").logoUrl("https://x/y.png").build();
        JsonNode node = Json.mapper().valueToTree(request);
        assertEquals(List.of("name", "slug", "logo_url"), iterate(node));
        assertTrue(Json.mapper().writeValueAsString(UserRegisterRequest.builder().email("e").password("p")
                .organizationName("Acme").build()).contains("\"organization_name\":\"Acme\""));
    }

    private static List<String> iterate(JsonNode node) {
        List<String> names = new java.util.ArrayList<>();
        node.fieldNames().forEachRemaining(names::add);
        return names;
    }

    @Test
    void crudCallsUseTheDocumentedMethodsAndPaths() {
        try (MockServer server = new MockServer()) {
            server.reply(r -> r.method().equals("DELETE") ? Reply.noContent() : Reply.ok("{\"id\":\"" + ID + "\"}"));
            NovaClient client = server.clientBuilder().tenantId(TENANT).build();
            client.contacts().create(ContactRequest.builder().email("a@b.co").build());
            client.contacts().update(ID, com.infimatrix.nova.models.PatchedContactRequest.builder().firstName("Ada").build());
            client.contacts().delete(ID);
            client.templates().activate(ID);
            client.templates().archive(ID);
            client.tenants().update(null, com.infimatrix.nova.models.PatchedTenantUpdateRequest.builder().name("N").build());
            client.tenants().delete(TENANT);
            assertEquals(List.of("POST /api/v1/contacts/", "PATCH /api/v1/contacts/" + ID + "/",
                    "DELETE /api/v1/contacts/" + ID + "/", "PATCH /api/v1/templates/" + ID + "/",
                    "PATCH /api/v1/templates/" + ID + "/", "PATCH /api/v1/tenants/" + TENANT + "/",
                    "DELETE /api/v1/tenants/" + TENANT + "/"),
                    server.requests().stream().map(r -> r.method() + " " + r.path()).toList());
            assertTrue(server.requests().get(3).bodyText().contains(TemplateStatusEnum.ACTIVE));
            assertTrue(server.requests().get(4).bodyText().contains(TemplateStatusEnum.ARCHIVED));
        }
    }

    @Test
    void deleteReturnsNormallyOn204() {
        try (MockServer server = new MockServer()) {
            server.reply(Reply.noContent());
            server.clientBuilder().build().webhooks().delete(ID);
            assertEquals("DELETE", server.last().method());
        }
    }

    @Test
    void notFoundIsTyped() {
        try (MockServer server = new MockServer()) {
            server.reply(Reply.error(404, "NOT_FOUND", "gone", "{}"));
            assertThrows(NovaNotFoundException.class, () -> server.clientBuilder().build().templates().get(ID));
        }
    }

    @Test
    void multipartUploadSendsFileAndFields(@TempDir Path dir) throws IOException {
        try (MockServer server = new MockServer()) {
            server.reply(Reply.created("{\"id\":\"f1\",\"name\":\"logo.png\",\"mime_type\":\"image/png\"}"));
            NovaClient client = server.clientBuilder().build();
            MediaAsset asset = client.assets().files().upload(FileUpload.of(new byte[] {1, 2, 3}, "logo.png"), ID);
            assertEquals("image/png", asset.mimeType());
            MockServer.Recorded r = server.last();
            assertTrue(r.header("content-type").startsWith("multipart/form-data; boundary="));
            String body = new String(r.body(), StandardCharsets.ISO_8859_1);
            assertTrue(body.contains("name=\"file\"; filename=\"logo.png\""));
            assertTrue(body.contains("Content-Type: image/png"));
            assertTrue(body.contains("name=\"folder\"") && body.contains(ID));

            Path file = dir.resolve("banner.jpg");
            Files.write(file, new byte[] {9, 9});
            client.assets().files().create(FileUpload.of(file), "Hero", null);
            String second = server.last().bodyText();
            assertTrue(second.contains("filename=\"banner.jpg\"") && second.contains("image/jpeg") && second.contains("Hero"));

            client.assets().files().upload(FileUpload.of(new ByteArrayInputStream("%PDF".getBytes(StandardCharsets.UTF_8)), "d.pdf"), null);
            assertTrue(server.last().bodyText().contains("application/pdf"));
        }
    }

    @Test
    void fileUploadValidatesItsInput() {
        assertThrows(NovaClientValidationException.class, () -> FileUpload.of(new byte[0], "a.png"));
        assertThrows(NovaClientValidationException.class, () -> FileUpload.of(new byte[] {1}, " "));
        assertThrows(NovaClientValidationException.class, () -> FileUpload.of(Path.of("/definitely/not/here.png")));
        assertEquals("application/octet-stream", FileUpload.of(new byte[] {1}, "blob.xyz").contentType());
        assertEquals("text/plain", FileUpload.of(new byte[] {1}, "a.png").withContentType("text/plain").contentType());
    }

    @Test
    void filenamesCannotInjectMultipartHeaders() {
        try (MockServer server = new MockServer()) {
            server.clientBuilder().build().assets().files()
                    .upload(FileUpload.of(new byte[] {1}, "a\"\r\nX-Evil: 1.png"), null);
            assertFalse(server.last().bodyText().contains("\r\nX-Evil: 1"));
        }
    }

    @Test
    void fileUpdateUsesFormEncoding() {
        try (MockServer server = new MockServer()) {
            server.clientBuilder().build().assets().files().update(ID, "new name", null);
            assertEquals("application/x-www-form-urlencoded", server.last().header("content-type"));
            assertEquals("name=new+name", server.last().bodyText());
        }
    }

    @Test
    void bulkUploadSendsCsv() {
        try (MockServer server = new MockServer()) {
            server.reply(Reply.ok("{\"created_count\":1,\"errors\":[],\"contacts\":[],\"message\":\"ok\"}"));
            var result = server.clientBuilder().build().contacts()
                    .bulkUpload(FileUpload.of("email\na@b.co\n".getBytes(StandardCharsets.UTF_8), "contacts.csv"));
            assertEquals(1, result.createdCount());
            assertTrue(server.last().bodyText().contains("Content-Type: text/csv"));
        }
    }

    @Test
    void csvExportsReturnTextAndBytes() {
        try (MockServer server = new MockServer()) {
            server.reply(Reply.text(200, "text/csv", "a,b\r\n1,2\r\n"));
            NovaClient client = server.clientBuilder().build();
            assertEquals("a,b\r\n1,2\r\n", client.emails().exportCsv(Query.builder().param("status", "FAILED").build()));
            assertEquals("status=FAILED", server.last().query());
            assertEquals(10, client.emails().exportCsvBytes(Query.empty()).length);
            assertEquals("a,b\r\n1,2\r\n", client.contacts().sampleTemplate());
        }
    }

    @Test
    void listsReturnedAsArraysAreTypedAndNullSafe() {
        try (MockServer server = new MockServer()) {
            NovaClient client = server.clientBuilder().build();
            server.reply(Reply.ok("[{\"key\":\"SMTP\",\"label\":\"SMTP\"}]"));
            assertEquals("SMTP", client.providers().types().get(0).key());
            server.reply(Reply.ok("[{\"key\":\"contact.created\",\"label\":\"x\"}]"));
            assertEquals(1, client.webhooks().events().size());
            server.reply(Reply.ok("null"));
            assertTrue(client.contacts().activity(ID).isEmpty());
        }
    }

    @Test
    void healthAndAnalyticsParseModels() {
        try (MockServer server = new MockServer()) {
            NovaClient client = server.clientBuilder().build();
            server.reply(Reply.ok("{\"status\":\"ok\",\"database\":\"healthy\"}"));
            assertEquals("ok", client.health().status());
            server.reply(Reply.ok("{\"total_contacts\":5}"));
            assertEquals(5L, client.analytics().dashboard("2026-01-01", null).totalContacts());
            assertEquals("date_from=2026-01-01", server.last().query());
        }
    }

    @Test
    void renderSendsVariables() throws IOException {
        try (MockServer server = new MockServer()) {
            server.reply(Reply.ok("{\"subject\":\"Hi Ada\"}"));
            server.clientBuilder().build().templates().render(ID, java.util.Map.of("name", "Ada"));
            assertEquals("Ada", json(server.last()).get("variables").get("name").asText());
        }
    }

    @Test
    void patchedRequestsDoNotSerializeUnsetFields() throws IOException {
        String text = Json.mapper().writeValueAsString(PatchedTemplateRequest.builder().name("W2").build());
        assertEquals("{\"name\":\"W2\"}", text);
    }
}
