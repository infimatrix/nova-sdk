import type { RequestOptions } from "../http.js";
import type { Page } from "../models.js";
import type {
  PatchedProviderConfigurationCreateUpdateRequest,
  ProviderConfiguration,
  ProviderConfigurationCreateUpdate,
  ProviderConfigurationCreateUpdateRequest,
  ProviderTestDispatch,
  ProviderTypeInfo,
  TestEmailProviderRequest,
} from "../schemas.js";
import { BaseResource, pathId, requireString, type ListQuery } from "./base.js";

/** Email service provider configurations. */
export class ProvidersResource extends BaseResource {
  /** `GET /api/v1/providers/` */
  list(query: ListQuery = {}, options: RequestOptions = {}): Promise<Page<ProviderConfiguration>> {
    return this.listPage<ProviderConfiguration>("providers/", { ...query }, options);
  }

  /** `GET /api/v1/providers/{id}/` */
  async get(providerId: string, options: RequestOptions = {}): Promise<ProviderConfiguration> {
    const res = await this.http.request<ProviderConfiguration>("GET", `providers/${pathId(providerId, "providerId")}/`, options);
    return res.data;
  }

  /** `POST /api/v1/providers/` */
  async create(
    body: ProviderConfigurationCreateUpdateRequest,
    options: RequestOptions = {},
  ): Promise<ProviderConfigurationCreateUpdate> {
    const res = await this.http.request<ProviderConfigurationCreateUpdate>("POST", "providers/", { ...options, json: body });
    return res.data;
  }

  /** `PATCH /api/v1/providers/{id}/` */
  async update(
    providerId: string,
    body: PatchedProviderConfigurationCreateUpdateRequest,
    options: RequestOptions = {},
  ): Promise<ProviderConfigurationCreateUpdate> {
    const res = await this.http.request<ProviderConfigurationCreateUpdate>(
      "PATCH",
      `providers/${pathId(providerId, "providerId")}/`,
      { ...options, json: body },
    );
    return res.data;
  }

  /** `DELETE /api/v1/providers/{id}/` */
  async delete(providerId: string, options: RequestOptions = {}): Promise<void> {
    await this.http.request("DELETE", `providers/${pathId(providerId, "providerId")}/`, options);
  }

  /** `GET /api/v1/providers/types/`: supported provider integration types. */
  async types(options: RequestOptions = {}): Promise<ProviderTypeInfo[]> {
    const res = await this.http.request<ProviderTypeInfo[]>("GET", "providers/types/", options);
    return Array.isArray(res.data) ? res.data : [];
  }

  /**
   * `POST /api/v1/providers/{id}/test/`: send a **real** test email through the provider.
   * Never retried automatically.
   */
  async test(providerId: string, body: TestEmailProviderRequest, options: RequestOptions = {}): Promise<ProviderTestDispatch> {
    const payload = { recipient_email: requireString(body.recipient_email, "recipient_email") };
    const res = await this.http.request<ProviderTestDispatch>("POST", `providers/${pathId(providerId, "providerId")}/test/`, {
      ...options,
      json: payload,
    });
    return res.data;
  }
}
