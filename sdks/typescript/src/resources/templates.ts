import type { RequestOptions } from "../http.js";
import type { Page } from "../models.js";
import type {
  PatchedTemplateRequest,
  Template,
  TemplateRender,
  TemplateRequest,
  TemplateStatusEnum,
} from "../schemas.js";
import { BaseResource, pathId, type ListQuery } from "./base.js";

export interface TemplateListQuery extends ListQuery {
  /** Filter by status (case-insensitive). */
  status?: TemplateStatusEnum | string;
}

/** Email template management. */
export class TemplatesResource extends BaseResource {
  /** `GET /api/v1/templates/` */
  list(query: TemplateListQuery = {}, options: RequestOptions = {}): Promise<Page<Template>> {
    return this.listPage<Template>("templates/", { ...query }, options);
  }

  /** `GET /api/v1/templates/{id}/` */
  async get(templateId: string, options: RequestOptions = {}): Promise<Template> {
    const res = await this.http.request<Template>("GET", `templates/${pathId(templateId, "templateId")}/`, options);
    return res.data;
  }

  /** `POST /api/v1/templates/` */
  async create(body: TemplateRequest, options: RequestOptions = {}): Promise<Template> {
    const res = await this.http.request<Template>("POST", "templates/", { ...options, json: body });
    return res.data;
  }

  /** `PATCH /api/v1/templates/{id}/` */
  async update(templateId: string, body: PatchedTemplateRequest, options: RequestOptions = {}): Promise<Template> {
    const res = await this.http.request<Template>("PATCH", `templates/${pathId(templateId, "templateId")}/`, {
      ...options,
      json: body,
    });
    return res.data;
  }

  /** `DELETE /api/v1/templates/{id}/` */
  async delete(templateId: string, options: RequestOptions = {}): Promise<void> {
    await this.http.request("DELETE", `templates/${pathId(templateId, "templateId")}/`, options);
  }

  /** `POST /api/v1/templates/{id}/render/`: render with variable values. */
  async render(
    templateId: string,
    variables: Record<string, unknown> = {},
    options: RequestOptions = {},
  ): Promise<TemplateRender> {
    const res = await this.http.request<TemplateRender>("POST", `templates/${pathId(templateId, "templateId")}/render/`, {
      ...options,
      json: { variables },
    });
    return res.data;
  }

  /** Set a template's status to `ACTIVE`. */
  activate(templateId: string, options: RequestOptions = {}): Promise<Template> {
    return this.update(templateId, { status: "ACTIVE" }, options);
  }

  /** Set a template's status to `ARCHIVED`. */
  archive(templateId: string, options: RequestOptions = {}): Promise<Template> {
    return this.update(templateId, { status: "ARCHIVED" }, options);
  }
}
