package com.infimatrix.nova;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.infimatrix.nova.errors.NovaClientValidationException;
import java.time.Duration;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.CsvSource;
import org.junit.jupiter.params.provider.ValueSource;

class ConfigTest {
    private static final String TENANT = "11111111-1111-1111-1111-111111111111";

    private static NovaClient.Builder base() {
        return NovaClient.builder().baseUrl("https://nova.example.com").apiKey("nova_key_x");
    }

    @Test
    void appliesDefaults() {
        NovaConfig config = base().build().config();
        assertEquals("https://nova.example.com", config.baseUrl());
        assertEquals(Duration.ofSeconds(30), config.requestTimeout());
        assertEquals(Duration.ofSeconds(10), config.connectTimeout());
        assertEquals(3, config.maxRetries());
        assertTrue(config.retryJitter());
    }

    @ParameterizedTest
    @CsvSource({
        "https://api.example.com/api/v1, https://api.example.com",
        "https://api.example.com/api/, https://api.example.com",
        "https://api.example.com///, https://api.example.com",
        "http://localhost:8000/, http://localhost:8000",
    })
    void normalizesBaseUrl(String input, String expected) {
        assertEquals(expected, base().baseUrl(input).build().config().baseUrl());
    }

    @ParameterizedTest
    @ValueSource(strings = {"ftp://x.example", "not a url", "https://", "", "  "})
    void rejectsBadBaseUrls(String url) {
        assertThrows(NovaClientValidationException.class, () -> base().baseUrl(url).build());
    }

    @Test
    void rejectsInvalidNumbers() {
        assertThrows(NovaClientValidationException.class, () -> base().maxRetries(-1).build());
        assertThrows(NovaClientValidationException.class, () -> base().maxRetries(11).build());
        assertThrows(NovaClientValidationException.class, () -> base().requestTimeout(Duration.ZERO).build());
        assertThrows(NovaClientValidationException.class, () -> base().connectTimeout(Duration.ofSeconds(-1)).build());
        assertThrows(NovaClientValidationException.class, () -> base().retryBackoff(Duration.ofMillis(-1)).build());
    }

    @Test
    void validatesAndCanonicalizesTenant() {
        assertEquals(TENANT, base().tenantId(TENANT.toUpperCase()).build().config().tenantId());
        assertThrows(NovaClientValidationException.class, () -> base().tenantId("nope").build());
        assertThrows(NovaClientValidationException.class, () -> base().build().withTenant("nope"));
    }

    @Test
    void stripsBearerPrefixesFromCredentials() {
        assertEquals("abc", NovaConfig.cleanCredential("  Bearer  Bearer abc "));
        assertEquals(null, NovaConfig.cleanCredential("bearer"));
        assertEquals(null, NovaConfig.cleanCredential("   "));
        assertEquals("k", base().apiKey("Bearer k").build().config().bearerCredential());
    }

    @Test
    void apiKeyWinsOverAccessToken() {
        assertEquals("key", base().apiKey("key").accessToken("jwt").build().config().bearerCredential());
        assertEquals("jwt", NovaClient.builder().baseUrl("https://x.example").accessToken("jwt").build().config().bearerCredential());
    }

    @Test
    void neverPrintsSecrets() {
        NovaClient client = base().apiKey("nova_key_supersecretvalue").accessToken("jwt-supersecret-token").build();
        String text = client + " " + client.config();
        assertFalse(text.contains("supersecret"));
        assertTrue(text.contains("[REDACTED]"));
    }

    @Test
    void derivedClientsAreIndependent() {
        NovaClient client = base().tenantId(TENANT).build();
        String other = "22222222-2222-2222-2222-222222222222";
        assertEquals(other, client.withTenant(other).config().tenantId());
        assertEquals(TENANT, client.config().tenantId());
        assertEquals("jwt", client.withApiKey(null).withAccessToken("jwt").config().bearerCredential());
    }
}
