package com.infimatrix.nova.resources;

import com.infimatrix.nova.Page;
import com.infimatrix.nova.Query;
import com.infimatrix.nova.errors.NovaClientValidationException;
import com.infimatrix.nova.http.ApiRequest;
import com.infimatrix.nova.http.HttpMethod;
import com.infimatrix.nova.http.HttpTransport;
import com.infimatrix.nova.models.Membership;
import com.infimatrix.nova.models.MembershipCreate;
import com.infimatrix.nova.models.MembershipCreateRequest;
import com.infimatrix.nova.models.MembershipUpdate;
import com.infimatrix.nova.models.PatchedMembershipUpdateRequest;
import com.infimatrix.nova.models.PatchedTenantUpdateRequest;
import com.infimatrix.nova.models.Tenant;
import com.infimatrix.nova.models.TenantCreate;
import com.infimatrix.nova.models.TenantCreateRequest;
import com.infimatrix.nova.models.TenantUpdate;

/** Tenants (organizations) and their memberships. */
public final class TenantsApi {
    private final HttpTransport http;
    private final MembershipsApi memberships;

    /** Creates the API; use {@code NovaClient#tenants()}. */
    public TenantsApi(HttpTransport http) {
        this.http = http;
        this.memberships = new MembershipsApi(http);
    }

    /** Membership bindings between users and a tenant. */
    public MembershipsApi memberships() {
        return memberships;
    }

    /** {@code GET /api/v1/tenants/}. */
    public Page<Tenant> list(Query query) {
        return http.listPage("tenants/", query, Tenant.class);
    }

    /** {@code POST /api/v1/tenants/}. */
    public TenantCreate create(TenantCreateRequest request) {
        return http.send(ApiRequest.of(HttpMethod.POST, "tenants/").json(request), TenantCreate.class);
    }

    /**
     * Returns the id of the tenant these credentials resolve to: the client's default tenant if one is set, otherwise
     * the tenant the server reports for the credentials ({@code GET /api/v1/auth/me/}).
     */
    public String currentTenantId() {
        return Validate.tenantOrLookup(http, null);
    }

    /**
     * {@code GET /api/v1/tenants/{id}/}. When {@code tenantId} is {@code null} the client's default tenant is used,
     * then the tenant the credentials resolve to.
     */
    public Tenant get(String tenantId) {
        return http.send(ApiRequest.of(HttpMethod.GET, "tenants/{}/", Validate.tenantOrLookup(http, tenantId)), Tenant.class);
    }

    /** {@code PATCH /api/v1/tenants/{id}/}. */
    public TenantUpdate update(String tenantId, PatchedTenantUpdateRequest request) {
        return http.send(ApiRequest.of(HttpMethod.PATCH, "tenants/{}/", Validate.tenantOrLookup(http, tenantId)).json(request),
                TenantUpdate.class);
    }

    /** {@code DELETE /api/v1/tenants/{id}/}. The id is never inferred: it must be passed or configured on the client. */
    public void delete(String tenantId) {
        http.send(ApiRequest.of(HttpMethod.DELETE, "tenants/{}/", Validate.tenant(http, tenantId)));
    }

    /** Membership operations of one tenant. */
    public static final class MembershipsApi {
        private final HttpTransport http;

        MembershipsApi(HttpTransport http) {
            this.http = http;
        }

        /** {@code GET /api/v1/tenants/{tenant_id}/members/}. */
        public Page<Membership> list(String tenantId, Query query) {
            return http.listPage("tenants/{}/members/", query, Membership.class, Validate.tenantOrLookup(http, tenantId));
        }

        /** {@code POST /api/v1/tenants/{tenant_id}/members/}. */
        public MembershipCreate add(String tenantId, MembershipCreateRequest request) {
            return http.send(
                    ApiRequest.of(HttpMethod.POST, "tenants/{}/members/", Validate.tenantOrLookup(http, tenantId)).json(request),
                    MembershipCreate.class);
        }

        /** {@code GET /api/v1/tenants/{tenant_id}/members/{id}/}. */
        public Membership get(String tenantId, String membershipId) {
            return http.send(ApiRequest.of(HttpMethod.GET, "tenants/{}/members/{}/", Validate.tenantOrLookup(http, tenantId),
                    Validate.nonBlank(membershipId, "membershipId")), Membership.class);
        }

        /** {@code PATCH /api/v1/tenants/{tenant_id}/members/{id}/}. */
        public MembershipUpdate update(String tenantId, String membershipId, PatchedMembershipUpdateRequest request) {
            if (request.role() == null && request.status() == null) {
                throw new NovaClientValidationException("Provide at least one of role or status.");
            }
            return http.send(ApiRequest.of(HttpMethod.PATCH, "tenants/{}/members/{}/", Validate.tenantOrLookup(http, tenantId),
                    Validate.nonBlank(membershipId, "membershipId")).json(request), MembershipUpdate.class);
        }

        /** {@code DELETE /api/v1/tenants/{tenant_id}/members/{id}/}. */
        public void remove(String tenantId, String membershipId) {
            http.send(ApiRequest.of(HttpMethod.DELETE, "tenants/{}/members/{}/", Validate.tenantOrLookup(http, tenantId),
                    Validate.nonBlank(membershipId, "membershipId")));
        }
    }
}
