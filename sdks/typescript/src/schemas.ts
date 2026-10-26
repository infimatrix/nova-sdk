/**
 * Nova API types.
 *
 * AUTO-GENERATED from openapi/nova-api.yaml by scripts/gen_ts_types.py.
 * Do not edit by hand; run the script to regenerate.
 */

/** A file payload accepted by upload endpoints. */
export type Binary = Blob | Uint8Array | ArrayBuffer;

/** Serializer for listing and reading user API Key records (without exposing raw secret key). */
export interface APIKey {
  id: string;
  name: string;
  key_prefix: string;
  is_active: boolean;
  created_at: string;
  expires_at: string | null;
  last_used_at: string | null;
}

/**
 * Serializer for creating a new API Key for the authenticated user.
 * Returns the raw unhashed API Key string ONCE upon successful creation.
 */
export interface APIKeyCreate {
  id: string;
  name?: string;
  key_prefix: string;
  api_key: string;
  is_active: boolean;
  expires_at?: string | null;
  created_at: string;
}

/**
 * Serializer for creating a new API Key for the authenticated user.
 * Returns the raw unhashed API Key string ONCE upon successful creation.
 */
export interface APIKeyCreateRequest {
  name?: string;
  expires_at?: string | null;
}

/**
 * Read-only serializer for access log entries.
 * Exposes all request metadata including HTTP method, path, status code,
 * category, action label, IP address, user agent, and response time.
 */
export interface AccessLog {
  id: string;
  workspace_name: string;
  user: string | null;
  user_email: string;
  user_name: string;
  created_by: string;
  client_code: string;
  category: CategoryEnum;
  category_display: string;
  /** Human-readable action label, e.g. 'User Login', 'Uploaded Asset'. */
  action: string;
  /** Optional detailed description of the activity. */
  description: string;
  http_method: string;
  path: string;
  query_string: string;
  status_code: number | null;
  ip_address: string | null;
  user_agent: string;
  /** Type of resource, e.g. 'MediaAsset', 'Contact', 'Template'. */
  resource_type: string;
  /** Primary key of the resource acted upon. */
  resource_id: string;
  /** Response time in milliseconds. */
  response_time_ms: number | null;
  /** Additional structured context about the activity. */
  metadata: unknown;
  created_at: string;
}

export interface AccessLogStats {
  total: number;
  last_24h: number;
  last_7d: number;
  /** Access-log count keyed by category. */
  category_breakdown: Record<string, unknown>;
  top_users: AccessLogTopUser[];
  avg_response_time_ms: number | null;
}

/**
 * Compact serializer for access log list views.
 * Provides fields specifically optimized for the frontend table view.
 */
export interface AccessLogSummary {
  id: string;
  workspace_name: string;
  ip_address: string;
  client_code: string;
  action: string;
  created_by: string;
  created_at: string;
  category: string;
  category_display: string;
  http_method: string;
  path: string;
  status_code: number;
  response_time_ms: number;
}

export interface AccessLogTopUser {
  user__email: string;
  activity_count: number;
}

export interface AssetFolder {
  id: string;
  name: string;
  slug: string;
  file_count: number;
  created_at: string;
  updated_at: string;
}

export interface AssetFolderRequest {
  name: string;
}

export type AuthenticationTypeEnum = "BASIC" | "NONE" | "OAUTH2";

export interface BulkContactDeleteRequest {
  contact_ids: string[];
}

export interface BulkContactDeleteResult {
  success: boolean;
  deleted_count: number;
}

export interface BulkContactUploadRequest {
  /** CSV file containing contact records */
  file: Binary;
}

export interface BulkContactUploadResult {
  message: string;
  created_count: number;
  /** Per-row failures: {row, error}. */
  errors: Record<string, unknown>[];
  contacts: Contact[];
}

export interface BulkSendEmailRequest {
  template_id: string;
  contact_ids: string[];
  fallback_variables?: Record<string, unknown>;
  sender_email: string;
  provider_id?: string | null;
}

export type CategoryEnum = "AUTH" | "CREATE" | "READ" | "UPDATE" | "DELETE" | "UPLOAD" | "DOWNLOAD" | "EXPORT" | "API_CALL" | "SYSTEM";

/** Serializer for changing current password for authenticated users. */
export interface ChangePasswordRequest {
  old_password: string;
  new_password: string;
  confirm_password: string;
}

export interface ChangePasswordResponse {
  detail: string;
  message: string;
}

export interface Contact {
  id: string;
  user_id?: string | null;
  /** User ID (e.g. USR001) */
  contact_id_str?: string | null;
  username?: string;
  email: string;
  first_name?: string;
  last_name?: string;
  country_code?: string;
  phone_number?: string;
  mobile_number: string;
  timezone?: string;
  status?: ContactStatusEnum;
  metadata?: unknown;
  created_at: string;
  updated_at: string;
}

export interface ContactActivity {
  id: string;
  title: string;
  subject: string;
  status: string;
  timestamp: string;
}

export interface ContactGroup {
  id: string;
  name: string;
  description?: string;
  contacts?: string[];
  created_at: string;
  updated_at: string;
}

export interface ContactGroupRequest {
  name: string;
  description?: string;
  contacts?: string[];
}

export interface ContactRequest {
  user_id?: string | null;
  /** User ID (e.g. USR001) */
  contact_id_str?: string | null;
  username?: string;
  email: string;
  first_name?: string;
  last_name?: string;
  country_code?: string;
  phone_number?: string;
  timezone?: string;
  status?: ContactStatusEnum;
  metadata?: unknown;
}

export type ContactStatusEnum = "SUBSCRIBED" | "UNSUBSCRIBED" | "BOUNCED";

export interface ContactSummary {
  id: string;
  user_id: string;
  /** User ID (e.g. USR001) */
  contact_id_str?: string | null;
  username?: string;
  email: string;
  first_name?: string;
  last_name?: string;
  /** Country calling code (e.g., +91, +1) */
  country_code?: string;
  /** Mobile / Phone number without country code */
  phone_number?: string;
  mobile_number: string;
  timezone?: string;
  status?: ContactStatusEnum;
  created_at: string;
}

/** Shape of the active tenant context (documentation of ``UserMe.current_tenant``). */
export interface CurrentTenant {
  id: string;
  name: string;
  slug: string;
  website: string;
  logo_url: string;
}

export interface DashboardAnalytics {
  total_contacts: number;
  new_contacts: number;
  email_overview: EmailOverview;
  recently_added_contacts: ContactSummary[];
  recently_failed_messages: RecentFailedMessage[];
}

export interface EmailBatchQueued {
  message: string;
  count: number;
}

export interface EmailLog {
  id: string;
  message_id: string;
  sender_name: string;
  sender_email: string;
  receiver_name: string;
  receiver_email: string;
  template_name: string;
  subject: string;
  note: string;
  status: EmailMessageStatusEnum;
  created_at: string;
}

export type EmailMessageStatusEnum = "PENDING" | "QUEUED" | "PROCESSING" | "SENT" | "DELIVERED" | "FAILED";

export interface EmailOverview {
  total_email: number;
  sent: number;
  delivered: number;
  opened: number;
  clicked: number;
  bounced: number;
  complaint: number;
  failed: number;
}

export interface EmailPreview {
  id: string;
  message_id: string;
  sender_name: string;
  sender_email: string;
  receiver_name: string;
  receiver_email: string;
  template_name: string;
  subject: string;
  note: string;
  status: EmailMessageStatusEnum;
  created_at: string;
  html_content?: string;
  text_content?: string;
  metadata?: unknown;
}

export type EventTypeEnum = "contact.created" | "contact.deleted" | "contact.updated" | "list.subscribed" | "list.unsubscribed" | "list.confirmed" | "list.resubscribed" | "list.bounced" | "list.complained" | "list.pending" | "list.removed" | "segment.joined" | "segment.left" | "email.sent" | "email.delivered" | "email.opened" | "email.clicked" | "email.bounced" | "email.complained" | "email.unsubscribed" | "custom_event.created" | "custom_event.updated" | "custom_event.deleted";

/** Serializer for requesting a password reset email instructions. */
export interface ForgotPasswordRequest {
  email: string;
}

export interface ForgotPasswordResponse {
  detail: string;
  message: string;
}

export interface GroupSendEmailRequest {
  template_id: string;
  group_id: string;
  fallback_variables?: Record<string, unknown>;
  sender_email: string;
  provider_id?: string | null;
}

export interface HealthStatus {
  /** Always `ok`. */
  status: string;
  /** `healthy` when the database responds. */
  database: string;
}

export interface HealthStatusDegraded {
  /** Always `degraded`. */
  status: string;
  /** Always `unhealthy`. */
  database: string;
}

export interface Login {
  access: string;
  refresh: string;
  user: User;
  tenants: TenantMembershipSummary[];
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface Logout {
  refresh: string;
}

export interface LogoutRequest {
  refresh: string;
}

export interface MediaAsset {
  id: string;
  folder?: string | null;
  folder_name: string;
  name: string;
  file: string;
  /** File size in bytes */
  file_size: number;
  formatted_file_size: string;
  mime_type: string;
  public_url: string;
  template_url: string;
  created_at: string;
  updated_at: string;
}

export interface MediaAssetRequest {
  folder?: string | null;
  name: string;
  file: Binary;
}

export interface MediaAssetUploadRequest {
  folder?: string | null;
  /** File asset to upload (PNG, JPG, SVG, WebP, PDF up to 10MB) */
  file: Binary;
}

export interface Membership {
  id: string;
  user_id: string;
  user_email: string;
  user_first_name: string;
  user_last_name: string;
  role?: RoleEnum;
  status?: MembershipStatusEnum;
  created_at: string;
  updated_at: string;
}

export interface MembershipCreate {
  role?: RoleEnum;
  status?: MembershipStatusEnum;
}

export interface MembershipCreateRequest {
  email: string;
  role?: RoleEnum;
  status?: MembershipStatusEnum;
}

export type MembershipStatusEnum = "ACTIVE" | "INACTIVE";

export interface MembershipUpdate {
  role?: RoleEnum;
  status?: MembershipStatusEnum;
}

export interface MembershipUpdateRequest {
  role?: RoleEnum;
  status?: MembershipStatusEnum;
}

export interface PatchedAssetFolderRequest {
  name?: string;
}

export interface PatchedContactGroupRequest {
  name?: string;
  description?: string;
  contacts?: string[];
}

export interface PatchedContactRequest {
  user_id?: string | null;
  /** User ID (e.g. USR001) */
  contact_id_str?: string | null;
  username?: string;
  email?: string;
  first_name?: string;
  last_name?: string;
  country_code?: string;
  phone_number?: string;
  timezone?: string;
  status?: ContactStatusEnum;
  metadata?: unknown;
}

export interface PatchedMediaAssetRequest {
  folder?: string | null;
  name?: string;
  file?: Binary;
}

export interface PatchedMembershipUpdateRequest {
  role?: RoleEnum;
  status?: MembershipStatusEnum;
}

export interface PatchedProviderConfigurationCreateUpdateRequest {
  name?: string;
  provider_type?: ProviderTypeEnum;
  senders?: SenderRequest[];
  smtp_host?: string;
  smtp_port?: number;
  tls_enabled?: boolean;
  authentication_type?: AuthenticationTypeEnum;
  smtp_user?: string;
  smtp_password?: string;
  /** AWS Region e.g. US East (N. Virginia) - us-east-1 */
  aws_region?: string;
  /** AWS Access Key ID */
  aws_access_key_id?: string;
  aws_secret_access_key?: string;
  /** Rate limit for marketing emails per minute */
  rate_limit_per_minute?: number;
  is_active?: boolean;
  /** Priority routing order (lower is higher priority) */
  priority?: number;
  /** Encrypted API keys and secrets */
  encrypted_credentials?: unknown;
}

export interface PatchedTemplateRequest {
  name?: string;
  subject?: string;
  description?: string;
  status?: TemplateStatusEnum;
  /** Action categories e.g. Onboarding */
  action_types?: unknown;
  /** Color and design settings for the template */
  design_config?: unknown;
  html_content?: string;
  text_content?: string;
  placeholders?: TemplatePlaceholderRequest[];
}

export interface PatchedTenantUpdateRequest {
  name?: string;
  /** Workspace domain / website URL */
  website?: string;
  /** Workspace logo / favicon URL */
  logo_url?: string;
  status?: TenantStatusEnum;
}

export interface PatchedTransactionalNotificationRequest {
  name?: string;
  /** Unique API identifier key (e.g. welcome_email) */
  api_identifier?: string;
  template_id?: string | null;
  /** Description of when this notification is triggered */
  description?: string;
}

export interface PatchedWebhookEndpointCreateUpdateRequest {
  name?: string;
  url?: string;
  events?: string[];
  is_active?: boolean;
}

export interface ProviderConfiguration {
  id: string;
  name: string;
  provider_type?: ProviderTypeEnum;
  senders?: Sender[];
  smtp_host?: string;
  smtp_port?: number;
  tls_enabled?: boolean;
  authentication_type?: AuthenticationTypeEnum;
  smtp_user?: string;
  has_password: boolean;
  /** AWS Region e.g. US East (N. Virginia) - us-east-1 */
  aws_region?: string;
  /** AWS Access Key ID */
  aws_access_key_id?: string;
  has_secret_key: boolean;
  /** Rate limit for marketing emails per minute */
  rate_limit_per_minute?: number;
  is_active?: boolean;
  /** Priority routing order (lower is higher priority) */
  priority?: number;
  created_at: string;
  updated_at: string;
}

export interface ProviderConfigurationCreateUpdate {
  id: string;
  name: string;
  provider_type?: ProviderTypeEnum;
  senders?: Sender[];
  smtp_host?: string;
  smtp_port?: number;
  tls_enabled?: boolean;
  authentication_type?: AuthenticationTypeEnum;
  smtp_user?: string;
  /** AWS Region e.g. US East (N. Virginia) - us-east-1 */
  aws_region?: string;
  /** AWS Access Key ID */
  aws_access_key_id?: string;
  /** Rate limit for marketing emails per minute */
  rate_limit_per_minute?: number;
  is_active?: boolean;
  /** Priority routing order (lower is higher priority) */
  priority?: number;
  /** Encrypted API keys and secrets */
  encrypted_credentials?: unknown;
}

export interface ProviderConfigurationCreateUpdateRequest {
  name: string;
  provider_type?: ProviderTypeEnum;
  senders?: SenderRequest[];
  smtp_host?: string;
  smtp_port?: number;
  tls_enabled?: boolean;
  authentication_type?: AuthenticationTypeEnum;
  smtp_user?: string;
  smtp_password?: string;
  /** AWS Region e.g. US East (N. Virginia) - us-east-1 */
  aws_region?: string;
  /** AWS Access Key ID */
  aws_access_key_id?: string;
  aws_secret_access_key?: string;
  /** Rate limit for marketing emails per minute */
  rate_limit_per_minute?: number;
  is_active?: boolean;
  /** Priority routing order (lower is higher priority) */
  priority?: number;
  /** Encrypted API keys and secrets */
  encrypted_credentials?: unknown;
}

export interface ProviderTestDispatch {
  success: boolean;
  message: string;
  message_id: string;
  task_id: string;
}

export type ProviderTypeEnum = "SMTP" | "AWS_SES" | "SENDGRID" | "MAILGUN" | "POSTMARK" | "MOCK";

export interface ProviderTypeInfo {
  key: string;
  label: string;
  description: string;
}

export interface RecentFailedMessage {
  id: string;
  recipient_email: string;
  subject: string;
  status?: EmailMessageStatusEnum;
  metadata?: unknown;
  created_at: string;
}

/** Serializer for confirming password reset via single-use reset token. */
export interface ResetPasswordRequest {
  uid?: string;
  uidb64?: string;
  token: string;
  new_password: string;
  confirm_password?: string;
}

export interface ResetPasswordResponse {
  detail: string;
  message: string;
}

export type RoleEnum = "PLATFORM_ADMIN" | "TENANT_ADMIN" | "TEMPLATE_MANAGER" | "CAMPAIGN_MANAGER" | "SENDER" | "VIEWER";

export interface SendEmailRequest {
  recipient_email: string;
  recipient_name?: string;
  sender_name?: string;
  sender_email?: string;
  subject: string;
  html_content?: string;
  text_content?: string;
  template_id?: string | null;
  template_name?: string;
  note?: string;
}

export interface SendTestEmailRequest {
  provider_id?: string;
  sender_email?: string;
  from_name?: string;
  recipient_email: string;
  cc_emails?: string;
  bcc_emails?: string;
  reply_to?: string;
  attachment?: Binary | null;
}

export interface Sender {
  name?: string;
  email: string;
  is_default?: boolean;
}

export interface SenderRequest {
  name?: string;
  email: string;
  is_default?: boolean;
}

export interface Template {
  id: string;
  name: string;
  slug: string;
  subject?: string;
  description?: string;
  status?: TemplateStatusEnum;
  /** Action categories e.g. Onboarding */
  action_types?: unknown;
  /** Color and design settings for the template */
  design_config?: unknown;
  html_content?: string;
  text_content?: string;
  placeholders?: TemplatePlaceholder[];
  created_at: string;
  updated_at: string;
}

export interface TemplatePlaceholder {
  id: number;
  name: string;
  default_value?: string;
  is_required?: boolean;
}

export interface TemplatePlaceholderRequest {
  name: string;
  default_value?: string;
  is_required?: boolean;
}

export interface TemplateRender {
  /** Variable key-values to render template */
  variables?: Record<string, unknown>;
}

export interface TemplateRenderRequest {
  /** Variable key-values to render template */
  variables?: Record<string, unknown>;
}

export interface TemplateRequest {
  name: string;
  subject?: string;
  description?: string;
  status?: TemplateStatusEnum;
  /** Action categories e.g. Onboarding */
  action_types?: unknown;
  /** Color and design settings for the template */
  design_config?: unknown;
  html_content?: string;
  text_content?: string;
  placeholders?: TemplatePlaceholderRequest[];
}

export type TemplateStatusEnum = "ACTIVE" | "DRAFT" | "ARCHIVED";

export interface Tenant {
  id: string;
  name: string;
  slug: string;
  /** Workspace domain / website URL */
  website?: string;
  /** Workspace logo / favicon URL */
  logo_url?: string;
  status?: TenantStatusEnum;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface TenantCreate {
  id: string;
  name: string;
  slug: string;
  /** Workspace domain / website URL */
  website?: string;
  /** Workspace logo / favicon URL */
  logo_url?: string;
  status?: TenantStatusEnum;
}

export interface TenantCreateRequest {
  name: string;
  slug: string;
  /** Workspace domain / website URL */
  website?: string;
  /** Workspace logo / favicon URL */
  logo_url?: string;
  status?: TenantStatusEnum;
}

export interface TenantMembershipSummary {
  id: string;
  name: string;
  slug: string;
  website: string;
  logo_url: string;
  role: string;
}

export type TenantStatusEnum = "ACTIVE" | "INACTIVE" | "SUSPENDED";

export interface TenantUpdate {
  name: string;
  /** Workspace domain / website URL */
  website?: string;
  /** Workspace logo / favicon URL */
  logo_url?: string;
  status?: TenantStatusEnum;
}

export interface TenantUpdateRequest {
  name: string;
  /** Workspace domain / website URL */
  website?: string;
  /** Workspace logo / favicon URL */
  logo_url?: string;
  status?: TenantStatusEnum;
}

export interface TestEmailProviderRequest {
  /** Recipient email address to receive the test email */
  recipient_email: string;
}

export interface TestWebhookRequest {
  event_type?: EventTypeEnum;
}

export interface TokenRefresh {
  access: string;
  refresh: string;
}

export interface TokenRefreshRequest {
  refresh: string;
}

export interface TransactionalNotification {
  id: string;
  /** Human-readable ID (e.g. ID001) */
  display_id: string;
  name: string;
  /** Unique API identifier key (e.g. welcome_email) */
  api_identifier: string;
  template_id?: string | null;
  template_name: string;
  /** Description of when this notification is triggered */
  description?: string;
  created_at: string;
  updated_at: string;
}

export interface TransactionalNotificationRequest {
  name: string;
  /** Unique API identifier key (e.g. welcome_email) */
  api_identifier: string;
  template_id?: string | null;
  /** Description of when this notification is triggered */
  description?: string;
}

export interface TransactionalTestDispatch {
  message: string;
  message_id: string;
  email_id: string;
}

export interface User {
  id: string;
  email: string;
  /** Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only. */
  username: string;
  first_name?: string;
  last_name?: string;
  /** Designates whether this user should be treated as active. Unselect this instead of deleting accounts. */
  is_active?: boolean;
  /** Designates whether the user can log into this admin site. */
  is_staff: boolean;
  /** Designates that this user has all permissions without explicitly assigning them. */
  is_superuser: boolean;
  created_at: string;
}

export interface UserMe {
  id: string;
  email: string;
  /** Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only. */
  username: string;
  first_name: string;
  last_name: string;
  /** Designates whether this user should be treated as active. Unselect this instead of deleting accounts. */
  is_active: boolean;
  /** Designates whether the user can log into this admin site. */
  is_staff: boolean;
  /** Designates that this user has all permissions without explicitly assigning them. */
  is_superuser: boolean;
  created_at: string;
  tenants: TenantMembershipSummary[];
  current_tenant: CurrentTenant | null;
  current_role: string | null;
}

export interface UserRegister {
  access: string;
  refresh: string;
  user: User;
  tenants: TenantMembershipSummary[];
}

export interface UserRegisterRequest {
  email: string;
  password: string;
  first_name?: string;
  last_name?: string;
  username?: string;
  organization_name?: string;
}

export interface UserRequest {
  email: string;
  /** Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only. */
  username: string;
  first_name?: string;
  last_name?: string;
  /** Designates whether this user should be treated as active. Unselect this instead of deleting accounts. */
  is_active?: boolean;
}

/** Serializer for checking validity of a password reset token before form submission. */
export interface ValidateResetTokenRequest {
  uid?: string;
  uidb64?: string;
  token: string;
}

export interface ValidateResetTokenResponse {
  valid: boolean;
  detail: string;
}

export interface WebhookEndpoint {
  id: string;
  name: string;
  url: string;
  /** Secret key used for HMAC payload signature verification */
  secret: string;
  secret_masked: string;
  /** List of subscribed event keys e.g. ['contact.created', 'email.delivered'] */
  events?: unknown;
  is_active?: boolean;
  created_at: string;
  updated_at: string;
}

export interface WebhookEndpointCreateUpdate {
  id: string;
  name: string;
  url: string;
  events?: string[];
  is_active?: boolean;
}

export interface WebhookEndpointCreateUpdateRequest {
  name: string;
  url: string;
  events?: string[];
  is_active?: boolean;
}

export interface WebhookEventChoice {
  key: string;
  label: string;
}

export interface WebhookSecretRotation {
  secret: string;
  message: string;
}

export interface WebhookTestDispatch {
  success: boolean;
  message: string;
  webhook_id: string;
  task_id: string;
  url: string;
  event_type: string;
}
