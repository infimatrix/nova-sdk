import { NovaValidationError } from "../errors.js";
import type { HttpTransport, RequestOptions } from "../http.js";
import type { Page } from "../models.js";
import type {
  Membership,
  MembershipCreate,
  MembershipCreateRequest,
  MembershipUpdate,
  PatchedMembershipUpdateRequest,
  PatchedTenantUpdateRequest,
  Tenant,
  TenantCreate,
  TenantCreateRequest,
  TenantUpdate,
} from "../schemas.js";
import { BaseResource, pathId, type ListQuery } from "./base.js";

type PageQuery = Pick<ListQuery, "page" | "page_size">;

/** Resolve a tenant ID from an explicit argument or the client default. */
type TenantResolver = (explicit?: string) => string;

/** Membership bindings between users and a tenant. */
export class TenantMembershipsResource extends BaseResource {
  constructor(
    http: HttpTransport,
    private readonly resolveTenant: TenantResolver,
  ) {
    super(http);
  }

  /** `GET /api/v1/tenants/{tenant_id}/members/` */
  list(tenantId?: string, query: PageQuery = {}, options: RequestOptions = {}): Promise<Page<Membership>> {
    return this.listPage<Membership>(`tenants/${this.resolveTenant(tenantId)}/members/`, { ...query }, options);
  }

  /** `POST /api/v1/tenants/{tenant_id}/members/` */
  async add(body: MembershipCreateRequest, tenantId?: string, options: RequestOptions = {}): Promise<MembershipCreate> {
    const res = await this.http.request<MembershipCreate>("POST", `tenants/${this.resolveTenant(tenantId)}/members/`, {
      ...options,
      json: body,
    });
    return res.data;
  }

  /** `GET /api/v1/tenants/{tenant_id}/members/{id}/` */
  async get(membershipId: string, tenantId?: string, options: RequestOptions = {}): Promise<Membership> {
    const res = await this.http.request<Membership>(
      "GET",
      `tenants/${this.resolveTenant(tenantId)}/members/${pathId(membershipId, "membershipId")}/`,
      options,
    );
    return res.data;
  }

  /** `PATCH /api/v1/tenants/{tenant_id}/members/{id}/` */
  async update(
    membershipId: string,
    body: PatchedMembershipUpdateRequest,
    tenantId?: string,
    options: RequestOptions = {},
  ): Promise<MembershipUpdate> {
    if (body.role === undefined && body.status === undefined) {
      throw new NovaValidationError("Provide at least one of role or status.");
    }
    const res = await this.http.request<MembershipUpdate>(
      "PATCH",
      `tenants/${this.resolveTenant(tenantId)}/members/${pathId(membershipId, "membershipId")}/`,
      { ...options, json: body },
    );
    return res.data;
  }

  /** `DELETE /api/v1/tenants/{tenant_id}/members/{id}/` */
  async remove(membershipId: string, tenantId?: string, options: RequestOptions = {}): Promise<void> {
    await this.http.request(
      "DELETE",
      `tenants/${this.resolveTenant(tenantId)}/members/${pathId(membershipId, "membershipId")}/`,
      options,
    );
  }
}

/** Tenant (organization/workspace) management. */
export class TenantsResource extends BaseResource {
  readonly memberships: TenantMembershipsResource;

  constructor(
    http: HttpTransport,
    private readonly resolveTenant: TenantResolver,
  ) {
    super(http);
    this.memberships = new TenantMembershipsResource(http, resolveTenant);
  }

  /** `GET /api/v1/tenants/` */
  list(query: PageQuery = {}, options: RequestOptions = {}): Promise<Page<Tenant>> {
    return this.listPage<Tenant>("tenants/", { ...query }, options);
  }

  /** `POST /api/v1/tenants/` */
  async create(body: TenantCreateRequest, options: RequestOptions = {}): Promise<TenantCreate> {
    const res = await this.http.request<TenantCreate>("POST", "tenants/", { ...options, json: body });
    return res.data;
  }

  /** `GET /api/v1/tenants/{id}/`. Defaults to the client's tenant. */
  async get(tenantId?: string, options: RequestOptions = {}): Promise<Tenant> {
    const res = await this.http.request<Tenant>("GET", `tenants/${this.resolveTenant(tenantId)}/`, options);
    return res.data;
  }

  /** `PATCH /api/v1/tenants/{id}/` */
  async update(body: PatchedTenantUpdateRequest, tenantId?: string, options: RequestOptions = {}): Promise<TenantUpdate> {
    const res = await this.http.request<TenantUpdate>("PATCH", `tenants/${this.resolveTenant(tenantId)}/`, {
      ...options,
      json: body,
    });
    return res.data;
  }

  /** `DELETE /api/v1/tenants/{id}/` */
  async delete(tenantId?: string, options: RequestOptions = {}): Promise<void> {
    await this.http.request("DELETE", `tenants/${this.resolveTenant(tenantId)}/`, options);
  }

  // Shortcuts mirroring the Python SDK
  listMembers(tenantId?: string, query: PageQuery = {}, options: RequestOptions = {}) {
    return this.memberships.list(tenantId, query, options);
  }
  addMember(body: MembershipCreateRequest, tenantId?: string, options: RequestOptions = {}) {
    return this.memberships.add(body, tenantId, options);
  }
  getMember(membershipId: string, tenantId?: string, options: RequestOptions = {}) {
    return this.memberships.get(membershipId, tenantId, options);
  }
  updateMember(
    membershipId: string,
    body: PatchedMembershipUpdateRequest,
    tenantId?: string,
    options: RequestOptions = {},
  ) {
    return this.memberships.update(membershipId, body, tenantId, options);
  }
  removeMember(membershipId: string, tenantId?: string, options: RequestOptions = {}) {
    return this.memberships.remove(membershipId, tenantId, options);
  }
}
