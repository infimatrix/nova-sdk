import { NovaValidationError } from "../errors.js";
import { buildUpload, type FileInput } from "../files.js";
import type { HttpTransport, RequestOptions } from "../http.js";
import type { Page } from "../models.js";
import type {
  BulkContactDeleteResult,
  BulkContactUploadResult,
  Contact,
  ContactActivity,
  ContactGroup,
  ContactGroupRequest,
  ContactRequest,
  PatchedContactGroupRequest,
  PatchedContactRequest,
} from "../schemas.js";
import { BaseResource, pathId, type ListQuery } from "./base.js";

/** Audience groups (lists). */
export class ContactGroupsResource extends BaseResource {
  /** `GET /api/v1/contacts/groups/` */
  list(query: ListQuery = {}, options: RequestOptions = {}): Promise<Page<ContactGroup>> {
    return this.listPage<ContactGroup>("contacts/groups/", { ...query }, options);
  }

  /** `GET /api/v1/contacts/groups/{id}/` */
  async get(groupId: string, options: RequestOptions = {}): Promise<ContactGroup> {
    const res = await this.http.request<ContactGroup>("GET", `contacts/groups/${pathId(groupId, "groupId")}/`, options);
    return res.data;
  }

  /** `POST /api/v1/contacts/groups/` */
  async create(body: ContactGroupRequest, options: RequestOptions = {}): Promise<ContactGroup> {
    const res = await this.http.request<ContactGroup>("POST", "contacts/groups/", { ...options, json: body });
    return res.data;
  }

  /** `PATCH /api/v1/contacts/groups/{id}/` */
  async update(groupId: string, body: PatchedContactGroupRequest, options: RequestOptions = {}): Promise<ContactGroup> {
    const res = await this.http.request<ContactGroup>("PATCH", `contacts/groups/${pathId(groupId, "groupId")}/`, {
      ...options,
      json: body,
    });
    return res.data;
  }

  /** `DELETE /api/v1/contacts/groups/{id}/` */
  async delete(groupId: string, options: RequestOptions = {}): Promise<void> {
    await this.http.request("DELETE", `contacts/groups/${pathId(groupId, "groupId")}/`, options);
  }
}

/** Contacts (recipients). */
export class ContactsResource extends BaseResource {
  readonly groups: ContactGroupsResource;

  constructor(http: HttpTransport) {
    super(http);
    this.groups = new ContactGroupsResource(http);
  }

  /** `GET /api/v1/contacts/`. `timezone` filters by exact (case-insensitive) timezone. */
  list(query: ListQuery & { timezone?: string } = {}, options: RequestOptions = {}): Promise<Page<Contact>> {
    return this.listPage<Contact>("contacts/", { ...query }, options);
  }

  /** `GET /api/v1/contacts/{id}/` */
  async get(contactId: string, options: RequestOptions = {}): Promise<Contact> {
    const res = await this.http.request<Contact>("GET", `contacts/${pathId(contactId, "contactId")}/`, options);
    return res.data;
  }

  /** `POST /api/v1/contacts/` */
  async create(body: ContactRequest, options: RequestOptions = {}): Promise<Contact> {
    const res = await this.http.request<Contact>("POST", "contacts/", { ...options, json: body });
    return res.data;
  }

  /** `PATCH /api/v1/contacts/{id}/` */
  async update(contactId: string, body: PatchedContactRequest, options: RequestOptions = {}): Promise<Contact> {
    const res = await this.http.request<Contact>("PATCH", `contacts/${pathId(contactId, "contactId")}/`, {
      ...options,
      json: body,
    });
    return res.data;
  }

  /** `DELETE /api/v1/contacts/{id}/` */
  async delete(contactId: string, options: RequestOptions = {}): Promise<void> {
    await this.http.request("DELETE", `contacts/${pathId(contactId, "contactId")}/`, options);
  }

  /** `POST /api/v1/contacts/bulk-delete/` */
  async bulkDelete(contactIds: string[], options: RequestOptions = {}): Promise<BulkContactDeleteResult> {
    if (!Array.isArray(contactIds) || contactIds.length === 0) {
      throw new NovaValidationError("contact_ids must be a non-empty list of IDs.");
    }
    const res = await this.http.request<BulkContactDeleteResult>("POST", "contacts/bulk-delete/", {
      ...options,
      json: { contact_ids: contactIds.map((id) => String(id).trim()) },
    });
    return res.data;
  }

  /** `GET /api/v1/contacts/{id}/activity/`: email/delivery timeline of a contact. */
  async activity(contactId: string, options: RequestOptions = {}): Promise<ContactActivity[]> {
    const res = await this.http.request<ContactActivity[]>("GET", `contacts/${pathId(contactId, "contactId")}/activity/`, options);
    return Array.isArray(res.data) ? res.data : [];
  }

  /** `GET /api/v1/contacts/sample-template/`: the CSV template for bulk uploads. */
  async sampleTemplate(options: RequestOptions = {}): Promise<string> {
    const res = await this.http.request<string>("GET", "contacts/sample-template/", options);
    return String(res.data ?? "");
  }

  /**
   * `POST /api/v1/contacts/bulk-upload/`: import contacts from a CSV file.
   * Server-side row problems are reported in the result's `errors`.
   */
  async bulkUpload(
    file: FileInput,
    uploadOptions: { filename?: string } = {},
    options: RequestOptions = {},
  ): Promise<BulkContactUploadResult> {
    const body = await buildUpload(file, {}, { filename: uploadOptions.filename ?? "contacts.csv", contentType: "text/csv" });
    const res = await this.http.request<BulkContactUploadResult>("POST", "contacts/bulk-upload/", { ...options, body });
    return res.data;
  }
}
