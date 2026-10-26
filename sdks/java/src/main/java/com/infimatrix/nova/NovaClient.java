package com.infimatrix.nova;

import com.infimatrix.nova.http.ApiRequest;
import com.infimatrix.nova.http.HttpMethod;
import com.infimatrix.nova.http.HttpTransport;
import com.infimatrix.nova.models.HealthStatus;
import com.infimatrix.nova.resources.AnalyticsApi;
import com.infimatrix.nova.resources.AssetsApi;
import com.infimatrix.nova.resources.AuditApi;
import com.infimatrix.nova.resources.AuthApi;
import com.infimatrix.nova.resources.CampaignsApi;
import com.infimatrix.nova.resources.ContactsApi;
import com.infimatrix.nova.resources.EmailsApi;
import com.infimatrix.nova.resources.ProvidersApi;
import com.infimatrix.nova.resources.TemplatesApi;
import com.infimatrix.nova.resources.TenantsApi;
import com.infimatrix.nova.resources.UsersApi;
import com.infimatrix.nova.resources.WebhooksApi;
import java.net.http.HttpClient;
import java.time.Duration;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Objects;

/**
 * Client for the Nova REST API.
 *
 * <pre>{@code
 * NovaClient nova = NovaClient.builder()
 *     .baseUrl("https://nova.example.com")
 *     .apiKey(System.getenv("NOVA_API_KEY"))
 *     .tenantId("00000000-0000-0000-0000-000000000001")
 *     .build();
 *
 * Page<Contact> page = nova.contacts().list(Query.builder().pageSize(50).build());
 * for (Contact contact : page) {   // walks every page lazily
 *     System.out.println(contact.email());
 * }
 * }</pre>
 *
 * <p>A client is <b>immutable and thread-safe</b>: create one, share it, and derive variants with
 * {@link #withTenant(String)}, {@link #withAccessToken(String)}, {@link #withApiKey(String)} or
 * {@link #with(RequestOptions)}. Variants share the underlying {@link HttpClient} and connection pool.
 *
 * <p>Use it from server-side code: API keys and tokens are secrets and must not be shipped inside client
 * applications (for example Android apps).
 */
public final class NovaClient {
    private final NovaConfig config;
    private final HttpClient httpClient;
    private final RequestOptions options;
    private final HttpTransport transport;

    private final AuthApi auth;
    private final UsersApi users;
    private final TenantsApi tenants;
    private final TemplatesApi templates;
    private final ContactsApi contacts;
    private final EmailsApi emails;
    private final ProvidersApi providers;
    private final WebhooksApi webhooks;
    private final CampaignsApi campaigns;
    private final AnalyticsApi analytics;
    private final AuditApi audit;
    private final AssetsApi assets;

    private NovaClient(NovaConfig config, HttpClient httpClient, RequestOptions options) {
        this.config = config;
        this.httpClient = httpClient;
        this.options = options;
        this.transport = new HttpTransport(config, httpClient, options);
        this.auth = new AuthApi(transport);
        this.users = new UsersApi(transport);
        this.tenants = new TenantsApi(transport);
        this.templates = new TemplatesApi(transport);
        this.contacts = new ContactsApi(transport);
        this.emails = new EmailsApi(transport);
        this.providers = new ProvidersApi(transport);
        this.webhooks = new WebhooksApi(transport);
        this.campaigns = new CampaignsApi(transport);
        this.analytics = new AnalyticsApi(transport);
        this.audit = new AuditApi(transport);
        this.assets = new AssetsApi(transport);
    }

    /** Returns a new builder. Unset options fall back to {@code NOVA_*} environment variables. */
    public static Builder builder() {
        return new Builder();
    }

    /** Authentication, account recovery and API keys. */
    public AuthApi auth() {
        return auth;
    }

    /** User profiles. */
    public UsersApi users() {
        return users;
    }

    /** Tenants and memberships. */
    public TenantsApi tenants() {
        return tenants;
    }

    /** Email templates. */
    public TemplatesApi templates() {
        return templates;
    }

    /** Contacts and contact groups. */
    public ContactsApi contacts() {
        return contacts;
    }

    /** Email dispatch and delivery logs. */
    public EmailsApi emails() {
        return emails;
    }

    /** Email provider configurations. */
    public ProvidersApi providers() {
        return providers;
    }

    /** Webhook endpoints. */
    public WebhooksApi webhooks() {
        return webhooks;
    }

    /** Transactional notifications. */
    public CampaignsApi campaigns() {
        return campaigns;
    }

    /** Dashboard metrics. */
    public AnalyticsApi analytics() {
        return analytics;
    }

    /** Access audit logs. */
    public AuditApi audit() {
        return audit;
    }

    /** Media library. */
    public AssetsApi assets() {
        return assets;
    }

    /** The configuration in effect (credentials are never printed). */
    public NovaConfig config() {
        return config;
    }

    /** The low-level transport, for endpoints newer than this SDK. */
    public HttpTransport transport() {
        return transport;
    }

    /** {@code GET /api/v1/health/}. */
    public HealthStatus health() {
        return transport.send(ApiRequest.of(HttpMethod.GET, "health/"), HealthStatus.class);
    }

    /** Returns a client scoped to another tenant. This client is unchanged, so it is safe under concurrency. */
    public NovaClient withTenant(String tenantId) {
        return new NovaClient(config.withTenant(tenantId), httpClient, options);
    }

    /** Returns a client that authenticates with another JWT access token. */
    public NovaClient withAccessToken(String accessToken) {
        return new NovaClient(config.withAccessToken(accessToken), httpClient, options);
    }

    /** Returns a client that authenticates with another API key. */
    public NovaClient withApiKey(String apiKey) {
        return new NovaClient(config.withApiKey(apiKey), httpClient, options);
    }

    /** Returns a client that applies {@code callOptions} (tenant, headers, correlation id, timeout) to every call. */
    public NovaClient with(RequestOptions callOptions) {
        return new NovaClient(config, httpClient, Objects.requireNonNull(callOptions));
    }

    @Override
    public String toString() {
        return "NovaClient(" + config + ")";
    }

    /** Builder for {@link NovaClient}. */
    public static final class Builder {
        private String baseUrl;
        private String apiKey;
        private String accessToken;
        private String tenantId;
        private Duration connectTimeout = Duration.ofSeconds(10);
        private Duration requestTimeout = Duration.ofSeconds(30);
        private int maxRetries = 3;
        private Duration retryBackoff = Duration.ofMillis(500);
        private boolean retryJitter = true;
        private final Map<String, String> defaultHeaders = new LinkedHashMap<>();
        private HttpClient httpClient;

        private Builder() {
        }

        /** API origin. Env {@code NOVA_BASE_URL}; default {@code http://localhost:8000}. A trailing {@code /api/v1} is stripped. */
        public Builder baseUrl(String value) {
            this.baseUrl = value;
            return this;
        }

        /** Nova API key ({@code nova_key_...}). Env {@code NOVA_API_KEY}. Takes precedence over the access token. */
        public Builder apiKey(String value) {
            this.apiKey = value;
            return this;
        }

        /** JWT access token. Env {@code NOVA_ACCESS_TOKEN}. */
        public Builder accessToken(String value) {
            this.accessToken = value;
            return this;
        }

        /** Default tenant UUID sent as {@code X-Tenant-ID}. Env {@code NOVA_TENANT_ID}. */
        public Builder tenantId(String value) {
            this.tenantId = value;
            return this;
        }

        /** Connect timeout (default 10 s). Ignored when a custom {@link HttpClient} is supplied. */
        public Builder connectTimeout(Duration value) {
            this.connectTimeout = value;
            return this;
        }

        /** Per-attempt request timeout (default 30 s). */
        public Builder requestTimeout(Duration value) {
            this.requestTimeout = value;
            return this;
        }

        /** Maximum retries of idempotent requests, 0 to 10 (default 3). */
        public Builder maxRetries(int value) {
            this.maxRetries = value;
            return this;
        }

        /** Exponential backoff base (default 500 ms). */
        public Builder retryBackoff(Duration value) {
            this.retryBackoff = value;
            return this;
        }

        /** Randomize backoff delays (default true). */
        public Builder retryJitter(boolean value) {
            this.retryJitter = value;
            return this;
        }

        /** Adds a header sent with every request. */
        public Builder defaultHeader(String name, String value) {
            this.defaultHeaders.put(name, value);
            return this;
        }

        /**
         * Uses a pre-configured {@link HttpClient} (proxy, TLS, executor). It must not follow redirects:
         * the SDK relies on {@link HttpClient.Redirect#NEVER} so credentials cannot leak across hosts.
         */
        public Builder httpClient(HttpClient value) {
            this.httpClient = value;
            return this;
        }

        /** Validates the configuration and builds the client. */
        public NovaClient build() {
            String url = baseUrl != null ? baseUrl : env("NOVA_BASE_URL", "http://localhost:8000");
            NovaConfig config = new NovaConfig(
                    url,
                    apiKey != null ? apiKey : env("NOVA_API_KEY", null),
                    accessToken != null ? accessToken : env("NOVA_ACCESS_TOKEN", null),
                    tenantId != null ? tenantId : env("NOVA_TENANT_ID", null),
                    connectTimeout, requestTimeout, maxRetries, retryBackoff, retryJitter, defaultHeaders);
            HttpClient client = httpClient != null ? httpClient : HttpClient.newBuilder()
                    .connectTimeout(config.connectTimeout())
                    .followRedirects(HttpClient.Redirect.NEVER)
                    .version(config.baseUrl().startsWith("https") ? HttpClient.Version.HTTP_2 : HttpClient.Version.HTTP_1_1)
                    .build();
            return new NovaClient(config, client, RequestOptions.none());
        }

        private static String env(String name, String fallback) {
            String value = System.getenv(name);
            return value == null || value.isBlank() ? fallback : value;
        }
    }
}
