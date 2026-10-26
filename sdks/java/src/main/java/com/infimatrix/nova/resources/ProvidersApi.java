package com.infimatrix.nova.resources;

import com.infimatrix.nova.Page;
import com.infimatrix.nova.Query;
import com.infimatrix.nova.http.ApiRequest;
import com.infimatrix.nova.http.HttpMethod;
import com.infimatrix.nova.http.HttpTransport;
import com.infimatrix.nova.models.PatchedProviderConfigurationCreateUpdateRequest;
import com.infimatrix.nova.models.ProviderConfiguration;
import com.infimatrix.nova.models.ProviderConfigurationCreateUpdate;
import com.infimatrix.nova.models.ProviderConfigurationCreateUpdateRequest;
import com.infimatrix.nova.models.ProviderTestDispatch;
import com.infimatrix.nova.models.ProviderTypeInfo;
import com.infimatrix.nova.models.TestEmailProviderRequest;
import java.util.List;

/** Email service provider configurations. */
public final class ProvidersApi {
    private final HttpTransport http;

    /** Creates the API; obtained from the client. */
    public ProvidersApi(HttpTransport http) {
        this.http = http;
    }

    /** {@code GET /api/v1/providers/}. */
    public Page<ProviderConfiguration> list(Query query) {
        return http.listPage("providers/", query, ProviderConfiguration.class);
    }

    /** {@code GET /api/v1/providers/{id}/}. */
    public ProviderConfiguration get(String providerId) {
        return http.send(ApiRequest.of(HttpMethod.GET, "providers/{}/", Validate.nonBlank(providerId, "providerId")),
                ProviderConfiguration.class);
    }

    /** {@code POST /api/v1/providers/}. */
    public ProviderConfigurationCreateUpdate create(ProviderConfigurationCreateUpdateRequest request) {
        return http.send(ApiRequest.of(HttpMethod.POST, "providers/").json(request), ProviderConfigurationCreateUpdate.class);
    }

    /** {@code PATCH /api/v1/providers/{id}/}. */
    public ProviderConfigurationCreateUpdate update(
            String providerId, PatchedProviderConfigurationCreateUpdateRequest request) {
        return http.send(ApiRequest.of(HttpMethod.PATCH, "providers/{}/", Validate.nonBlank(providerId, "providerId"))
                .json(request), ProviderConfigurationCreateUpdate.class);
    }

    /** {@code DELETE /api/v1/providers/{id}/}. */
    public void delete(String providerId) {
        http.send(ApiRequest.of(HttpMethod.DELETE, "providers/{}/", Validate.nonBlank(providerId, "providerId")));
    }

    /** {@code GET /api/v1/providers/types/}: supported integration types. */
    public List<ProviderTypeInfo> types() {
        return http.sendList(ApiRequest.of(HttpMethod.GET, "providers/types/"), ProviderTypeInfo.class);
    }

    /** {@code POST /api/v1/providers/{id}/test/}: sends a <b>real</b> test email. Never retried automatically. */
    public ProviderTestDispatch test(String providerId, String recipientEmail) {
        return http.send(ApiRequest.of(HttpMethod.POST, "providers/{}/test/", Validate.nonBlank(providerId, "providerId"))
                .json(TestEmailProviderRequest.builder()
                        .recipientEmail(Validate.nonBlank(recipientEmail, "recipient_email")).build()),
                ProviderTestDispatch.class);
    }
}
