package com.infimatrix.nova.resources;

import com.infimatrix.nova.Page;
import com.infimatrix.nova.Query;
import com.infimatrix.nova.errors.NovaClientValidationException;
import com.infimatrix.nova.http.ApiRequest;
import com.infimatrix.nova.http.HttpMethod;
import com.infimatrix.nova.http.HttpTransport;
import com.infimatrix.nova.models.APIKey;
import com.infimatrix.nova.models.APIKeyCreate;
import com.infimatrix.nova.models.APIKeyCreateRequest;
import com.infimatrix.nova.models.ChangePasswordRequest;
import com.infimatrix.nova.models.ChangePasswordResponse;
import com.infimatrix.nova.models.ForgotPasswordRequest;
import com.infimatrix.nova.models.ForgotPasswordResponse;
import com.infimatrix.nova.models.Login;
import com.infimatrix.nova.models.LoginRequest;
import com.infimatrix.nova.models.Logout;
import com.infimatrix.nova.models.LogoutRequest;
import com.infimatrix.nova.models.ResetPasswordRequest;
import com.infimatrix.nova.models.ResetPasswordResponse;
import com.infimatrix.nova.models.TokenRefresh;
import com.infimatrix.nova.models.TokenRefreshRequest;
import com.infimatrix.nova.models.UserMe;
import com.infimatrix.nova.models.UserRegister;
import com.infimatrix.nova.models.UserRegisterRequest;
import com.infimatrix.nova.models.ValidateResetTokenRequest;
import com.infimatrix.nova.models.ValidateResetTokenResponse;

/** Authentication, account recovery and API keys. */
public final class AuthApi {
    private final HttpTransport http;
    private final ApiKeysApi apiKeys;

    /** Creates the API; use {@code NovaClient#auth()}. */
    public AuthApi(HttpTransport http) {
        this.http = http;
        this.apiKeys = new ApiKeysApi(http);
    }

    /** API key management for the authenticated user. */
    public ApiKeysApi apiKeys() {
        return apiKeys;
    }

    /**
     * {@code POST /api/v1/auth/login/}. To use the returned token, call
     * {@code client.withAccessToken(login.access())}.
     */
    public Login login(String email, String password) {
        LoginRequest body = LoginRequest.builder()
                .email(Validate.nonBlank(email, "email")).password(requirePassword(password, "password")).build();
        return http.send(ApiRequest.of(HttpMethod.POST, "auth/login/").json(body), Login.class);
    }

    /** {@code POST /api/v1/auth/register/}: creates an account (and optionally an organization). */
    public UserRegister register(UserRegisterRequest request) {
        UserRegisterRequest body = UserRegisterRequest.builder()
                .email(Validate.nonBlank(request.email(), "email"))
                .password(requirePassword(request.password(), "password"))
                .firstName(request.firstName()).lastName(request.lastName()).username(request.username())
                .organizationName(request.organizationName()).build();
        return http.send(ApiRequest.of(HttpMethod.POST, "auth/register/").json(body), UserRegister.class);
    }

    /** {@code POST /api/v1/auth/refresh/}. */
    public TokenRefresh refresh(String refreshToken) {
        TokenRefreshRequest body = TokenRefreshRequest.builder()
                .refresh(Validate.nonBlank(refreshToken, "refreshToken")).build();
        return http.send(ApiRequest.of(HttpMethod.POST, "auth/refresh/").json(body), TokenRefresh.class);
    }

    /** {@code POST /api/v1/auth/logout/}: blacklists a refresh token. */
    public Logout logout(String refreshToken) {
        LogoutRequest body = LogoutRequest.builder().refresh(Validate.nonBlank(refreshToken, "refreshToken")).build();
        return http.send(ApiRequest.of(HttpMethod.POST, "auth/logout/").json(body), Logout.class);
    }

    /** {@code GET /api/v1/auth/me/}. */
    public UserMe me() {
        return http.send(ApiRequest.of(HttpMethod.GET, "auth/me/"), UserMe.class);
    }

    /** {@code POST /api/v1/auth/forgot-password/}: requests a reset email (the response is always generic). */
    public ForgotPasswordResponse forgotPassword(String email) {
        ForgotPasswordRequest body = ForgotPasswordRequest.builder().email(Validate.nonBlank(email, "email")).build();
        return http.send(ApiRequest.of(HttpMethod.POST, "auth/forgot-password/").json(body), ForgotPasswordResponse.class);
    }

    /** {@code POST /api/v1/auth/reset-password/validate/}: checks a reset link's {@code uid} and {@code token}. */
    public ValidateResetTokenResponse validateResetToken(String uid, String token) {
        ValidateResetTokenRequest body = ValidateResetTokenRequest.builder()
                .uid(Validate.nonBlank(uid, "uid")).token(Validate.nonBlank(token, "token")).build();
        return http.send(ApiRequest.of(HttpMethod.POST, "auth/reset-password/validate/").json(body),
                ValidateResetTokenResponse.class);
    }

    /** {@code POST /api/v1/auth/reset-password/}: completes a reset with the {@code uid} and {@code token} from the email. */
    public ResetPasswordResponse resetPassword(ResetPasswordRequest request) {
        String uid = request.uid() != null ? request.uid() : request.uidb64();
        ResetPasswordRequest body = ResetPasswordRequest.builder()
                .uid(Validate.nonBlank(uid, "uid")).token(Validate.nonBlank(request.token(), "token"))
                .newPassword(requirePassword(request.newPassword(), "new_password"))
                .confirmPassword(request.confirmPassword()).build();
        return http.send(ApiRequest.of(HttpMethod.POST, "auth/reset-password/").json(body), ResetPasswordResponse.class);
    }

    /** {@code POST /api/v1/auth/change-password/}. */
    public ChangePasswordResponse changePassword(String oldPassword, String newPassword, String confirmPassword) {
        ChangePasswordRequest body = ChangePasswordRequest.builder()
                .oldPassword(requirePassword(oldPassword, "old_password"))
                .newPassword(requirePassword(newPassword, "new_password"))
                .confirmPassword(requirePassword(confirmPassword, "confirm_password")).build();
        return http.send(ApiRequest.of(HttpMethod.POST, "auth/change-password/").json(body), ChangePasswordResponse.class);
    }

    private static String requirePassword(String value, String label) {
        if (value == null || value.isEmpty()) {
            throw new NovaClientValidationException(label + " must be a non-empty string.");
        }
        return value;
    }

    /** API keys of the authenticated user. */
    public static final class ApiKeysApi {
        private final HttpTransport http;

        ApiKeysApi(HttpTransport http) {
            this.http = http;
        }

        /** {@code GET /api/v1/auth/api-keys/}. */
        public Page<APIKey> list(Query query) {
            return http.listPage("auth/api-keys/", query, APIKey.class);
        }

        /** {@code POST /api/v1/auth/api-keys/}. The raw key is returned <b>once</b>. */
        public APIKeyCreate create(String name) {
            APIKeyCreateRequest body = APIKeyCreateRequest.builder()
                    .name(name == null ? "Default API Key" : Validate.nonBlank(name, "name")).build();
            return http.send(ApiRequest.of(HttpMethod.POST, "auth/api-keys/").json(body), APIKeyCreate.class);
        }

        /** {@code DELETE /api/v1/auth/api-keys/{id}/}. */
        public void revoke(String apiKeyId) {
            http.send(ApiRequest.of(HttpMethod.DELETE, "auth/api-keys/{}/", Validate.nonBlank(apiKeyId, "apiKeyId")));
        }
    }
}
