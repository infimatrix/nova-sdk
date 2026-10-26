package com.infimatrix.nova.resources;

import com.infimatrix.nova.Page;
import com.infimatrix.nova.Query;
import com.infimatrix.nova.http.ApiRequest;
import com.infimatrix.nova.http.HttpMethod;
import com.infimatrix.nova.http.HttpTransport;
import com.infimatrix.nova.models.User;
import com.infimatrix.nova.models.UserMe;

/** User profiles within the active tenant. */
public final class UsersApi {
    private final HttpTransport http;

    /** Creates the API; use {@code NovaClient#users()}. */
    public UsersApi(HttpTransport http) {
        this.http = http;
    }

    /** {@code GET /api/v1/users/}. */
    public Page<User> list(Query query) {
        return http.listPage("users/", query, User.class);
    }

    /** {@code GET /api/v1/users/me/}. */
    public UserMe me() {
        return http.send(ApiRequest.of(HttpMethod.GET, "users/me/"), UserMe.class);
    }
}
