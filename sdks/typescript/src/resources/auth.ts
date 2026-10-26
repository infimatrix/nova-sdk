import type { RequestOptions } from "../http.js";
import type { Page } from "../models.js";
import type {
  APIKey,
  APIKeyCreate,
  APIKeyCreateRequest,
  ChangePasswordRequest,
  ChangePasswordResponse,
  ForgotPasswordResponse,
  Login,
  LoginRequest,
  Logout,
  ResetPasswordRequest,
  ResetPasswordResponse,
  TokenRefresh,
  UserMe,
  UserRegister,
  UserRegisterRequest,
  ValidateResetTokenResponse,
} from "../schemas.js";
import { BaseResource, pathId, requireString, type ListQuery } from "./base.js";
import { NovaValidationError } from "../errors.js";
import type { HttpTransport } from "../http.js";

/** Options for calls that can store the returned access token on the client. */
export interface TokenOptions extends RequestOptions {
  /** Use the returned access token for subsequent requests on this client. */
  setCurrentToken?: boolean;
}

/** API key management for the authenticated user. */
export class APIKeysResource extends BaseResource {
  /** `GET /api/v1/auth/api-keys/` */
  list(query: Pick<ListQuery, "page" | "page_size"> = {}, options: RequestOptions = {}): Promise<Page<APIKey>> {
    return this.listPage<APIKey>("auth/api-keys/", { ...query }, options);
  }

  /** `POST /api/v1/auth/api-keys/`. The raw key is returned **once**. */
  async create(body: APIKeyCreateRequest = {}, options: RequestOptions = {}): Promise<APIKeyCreate> {
    const payload = { ...body, name: body.name === undefined ? "Default API Key" : requireString(body.name, "name") };
    const res = await this.http.request<APIKeyCreate>("POST", "auth/api-keys/", { ...options, json: payload });
    return res.data;
  }

  /** `DELETE /api/v1/auth/api-keys/{id}/` */
  async revoke(apiKeyId: string, options: RequestOptions = {}): Promise<void> {
    await this.http.request("DELETE", `auth/api-keys/${pathId(apiKeyId, "apiKeyId")}/`, options);
  }
}

/** Authentication, account recovery and the current user. */
export class AuthResource extends BaseResource {
  readonly apiKeys: APIKeysResource;

  constructor(
    http: HttpTransport,
    private readonly setToken: (token: string | undefined) => void,
  ) {
    super(http);
    this.apiKeys = new APIKeysResource(http);
  }

  /** `POST /api/v1/auth/login/` */
  async login(body: LoginRequest, options: TokenOptions = {}): Promise<Login> {
    const payload = { email: requireString(body.email, "email"), password: requirePassword(body.password, "password") };
    const { setCurrentToken, ...requestOptions } = options;
    const res = await this.http.request<Login>("POST", "auth/login/", { ...requestOptions, json: payload });
    if (setCurrentToken && res.data?.access) this.setToken(res.data.access);
    return res.data;
  }

  /** `POST /api/v1/auth/register/`: create an account (and optionally an organization). */
  async register(body: UserRegisterRequest, options: TokenOptions = {}): Promise<UserRegister> {
    const payload = { ...body, email: requireString(body.email, "email"), password: requirePassword(body.password, "password") };
    const { setCurrentToken, ...requestOptions } = options;
    const res = await this.http.request<UserRegister>("POST", "auth/register/", { ...requestOptions, json: payload });
    if (setCurrentToken && res.data?.access) this.setToken(res.data.access);
    return res.data;
  }

  /** `POST /api/v1/auth/refresh/` */
  async refresh(refreshToken: string, options: RequestOptions = {}): Promise<TokenRefresh> {
    const res = await this.http.request<TokenRefresh>("POST", "auth/refresh/", {
      ...options,
      json: { refresh: requireString(refreshToken, "refreshToken") },
    });
    return res.data;
  }

  /** `POST /api/v1/auth/logout/`: blacklist a refresh token. */
  async logout(refreshToken: string, options: RequestOptions = {}): Promise<Logout> {
    const res = await this.http.request<Logout>("POST", "auth/logout/", {
      ...options,
      json: { refresh: requireString(refreshToken, "refreshToken") },
    });
    return res.data;
  }

  /** `GET /api/v1/auth/me/` */
  async me(options: RequestOptions = {}): Promise<UserMe> {
    const res = await this.http.request<UserMe>("GET", "auth/me/", options);
    return res.data;
  }

  /** `POST /api/v1/auth/forgot-password/`: request a reset email (the response is always generic). */
  async forgotPassword(email: string, options: RequestOptions = {}): Promise<ForgotPasswordResponse> {
    const res = await this.http.request<ForgotPasswordResponse>("POST", "auth/forgot-password/", {
      ...options,
      json: { email: requireString(email, "email") },
    });
    return res.data;
  }

  /** `POST /api/v1/auth/reset-password/validate/`: check a reset link's `uid` and `token`. */
  async validateResetToken(
    params: { uid: string; token: string },
    options: RequestOptions = {},
  ): Promise<ValidateResetTokenResponse> {
    const res = await this.http.request<ValidateResetTokenResponse>("POST", "auth/reset-password/validate/", {
      ...options,
      json: { uid: requireString(params.uid, "uid"), token: requireString(params.token, "token") },
    });
    return res.data;
  }

  /** `POST /api/v1/auth/reset-password/`: complete a reset with the `uid` and `token` from the email. */
  async resetPassword(body: ResetPasswordRequest, options: RequestOptions = {}): Promise<ResetPasswordResponse> {
    const uid = body.uid ?? body.uidb64;
    if (!uid) throw new NovaValidationError("uid must be a non-empty string.");
    const payload: ResetPasswordRequest = {
      uid: requireString(uid, "uid"),
      token: requireString(body.token, "token"),
      new_password: requirePassword(body.new_password, "new_password"),
    };
    if (body.confirm_password !== undefined) payload.confirm_password = body.confirm_password;
    const res = await this.http.request<ResetPasswordResponse>("POST", "auth/reset-password/", {
      ...options,
      json: payload,
    });
    return res.data;
  }

  /** `POST /api/v1/auth/change-password/` */
  async changePassword(body: ChangePasswordRequest, options: RequestOptions = {}): Promise<ChangePasswordResponse> {
    const payload: ChangePasswordRequest = {
      old_password: requirePassword(body.old_password, "old_password"),
      new_password: requirePassword(body.new_password, "new_password"),
      confirm_password: requirePassword(body.confirm_password, "confirm_password"),
    };
    const res = await this.http.request<ChangePasswordResponse>("POST", "auth/change-password/", {
      ...options,
      json: payload,
    });
    return res.data;
  }
}

function requirePassword(value: unknown, label: string): string {
  if (typeof value !== "string" || !value) throw new NovaValidationError(`${label} must be a non-empty string.`);
  return value;
}
