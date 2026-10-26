package com.infimatrix.nova.resources;

import com.infimatrix.nova.Page;
import com.infimatrix.nova.Query;
import com.infimatrix.nova.http.ApiRequest;
import com.infimatrix.nova.http.HttpMethod;
import com.infimatrix.nova.http.HttpTransport;
import com.infimatrix.nova.models.PatchedTemplateRequest;
import com.infimatrix.nova.models.Template;
import com.infimatrix.nova.models.TemplateRender;
import com.infimatrix.nova.models.TemplateRenderRequest;
import com.infimatrix.nova.models.TemplateRequest;
import com.infimatrix.nova.models.TemplateStatusEnum;
import java.util.Map;

/** Email templates. */
public final class TemplatesApi {
    private final HttpTransport http;

    /** Creates the API; obtained from the client. */
    public TemplatesApi(HttpTransport http) {
        this.http = http;
    }

    /** {@code GET /api/v1/templates/}. */
    public Page<Template> list(Query query) {
        return http.listPage("templates/", query, Template.class);
    }

    /** {@code GET /api/v1/templates/{id}/}. */
    public Template get(String templateId) {
        return http.send(ApiRequest.of(HttpMethod.GET, "templates/{}/", Validate.nonBlank(templateId, "templateId")),
                Template.class);
    }

    /** {@code POST /api/v1/templates/}. */
    public Template create(TemplateRequest request) {
        return http.send(ApiRequest.of(HttpMethod.POST, "templates/").json(request), Template.class);
    }

    /** {@code PATCH /api/v1/templates/{id}/}. */
    public Template update(String templateId, PatchedTemplateRequest request) {
        return http.send(ApiRequest.of(HttpMethod.PATCH, "templates/{}/", Validate.nonBlank(templateId, "templateId"))
                .json(request), Template.class);
    }

    /** {@code DELETE /api/v1/templates/{id}/}. */
    public void delete(String templateId) {
        http.send(ApiRequest.of(HttpMethod.DELETE, "templates/{}/", Validate.nonBlank(templateId, "templateId")));
    }

    /** {@code POST /api/v1/templates/{id}/render/}: renders with variable values. */
    public TemplateRender render(String templateId, Map<String, Object> variables) {
        return http.send(ApiRequest.of(HttpMethod.POST, "templates/{}/render/", Validate.nonBlank(templateId, "templateId"))
                .json(new TemplateRenderRequest(variables == null ? Map.of() : variables)), TemplateRender.class);
    }

    /** Sets a template's status to {@code ACTIVE}. */
    public Template activate(String templateId) {
        return update(templateId, PatchedTemplateRequest.builder().status(TemplateStatusEnum.ACTIVE).build());
    }

    /** Sets a template's status to {@code ARCHIVED}. */
    public Template archive(String templateId) {
        return update(templateId, PatchedTemplateRequest.builder().status(TemplateStatusEnum.ARCHIVED).build());
    }
}
