import type { RequestOptions } from "../http.js";
import type { Page } from "../models.js";
import type { User, UserMe } from "../schemas.js";
import { BaseResource, type ListQuery } from "./base.js";

/** User profiles within the active tenant. */
export class UsersResource extends BaseResource {
  /** `GET /api/v1/users/` */
  list(query: Pick<ListQuery, "page" | "page_size"> = {}, options: RequestOptions = {}): Promise<Page<User>> {
    return this.listPage<User>("users/", { ...query }, options);
  }

  /** `GET /api/v1/users/me/` */
  async me(options: RequestOptions = {}): Promise<UserMe> {
    const res = await this.http.request<UserMe>("GET", "users/me/", options);
    return res.data;
  }
}
