package com.infimatrix.nova.resources;

import com.infimatrix.nova.FileUpload;
import com.infimatrix.nova.Page;
import com.infimatrix.nova.Query;
import com.infimatrix.nova.errors.NovaClientValidationException;
import com.infimatrix.nova.http.ApiRequest;
import com.infimatrix.nova.http.HttpMethod;
import com.infimatrix.nova.http.HttpTransport;
import com.infimatrix.nova.models.BulkContactDeleteRequest;
import com.infimatrix.nova.models.BulkContactDeleteResult;
import com.infimatrix.nova.models.BulkContactUploadResult;
import com.infimatrix.nova.models.Contact;
import com.infimatrix.nova.models.ContactActivity;
import com.infimatrix.nova.models.ContactGroup;
import com.infimatrix.nova.models.ContactGroupRequest;
import com.infimatrix.nova.models.ContactRequest;
import com.infimatrix.nova.models.PatchedContactGroupRequest;
import com.infimatrix.nova.models.PatchedContactRequest;
import java.util.List;
import java.util.Map;

/** Contacts (recipients) and contact groups. */
public final class ContactsApi {
    private final HttpTransport http;
    private final GroupsApi groups;

    /** Creates the API; use {@code NovaClient#contacts()}. */
    public ContactsApi(HttpTransport http) {
        this.http = http;
        this.groups = new GroupsApi(http);
    }

    /** Audience groups. */
    public GroupsApi groups() {
        return groups;
    }

    /** {@code GET /api/v1/contacts/}; {@code timezone} filters via {@code Query.builder().param("timezone", ...)}. */
    public Page<Contact> list(Query query) {
        return http.listPage("contacts/", query, Contact.class);
    }

    /** {@code GET /api/v1/contacts/{id}/}. */
    public Contact get(String contactId) {
        return http.send(ApiRequest.of(HttpMethod.GET, "contacts/{}/", Validate.nonBlank(contactId, "contactId")),
                Contact.class);
    }

    /** {@code POST /api/v1/contacts/}. */
    public Contact create(ContactRequest request) {
        return http.send(ApiRequest.of(HttpMethod.POST, "contacts/").json(request), Contact.class);
    }

    /** {@code PATCH /api/v1/contacts/{id}/}. */
    public Contact update(String contactId, PatchedContactRequest request) {
        return http.send(ApiRequest.of(HttpMethod.PATCH, "contacts/{}/", Validate.nonBlank(contactId, "contactId"))
                .json(request), Contact.class);
    }

    /** {@code DELETE /api/v1/contacts/{id}/}. */
    public void delete(String contactId) {
        http.send(ApiRequest.of(HttpMethod.DELETE, "contacts/{}/", Validate.nonBlank(contactId, "contactId")));
    }

    /** {@code POST /api/v1/contacts/bulk-delete/}. */
    public BulkContactDeleteResult bulkDelete(List<String> contactIds) {
        if (contactIds == null || contactIds.isEmpty()) {
            throw new NovaClientValidationException("contact_ids must be a non-empty list of IDs.");
        }
        return http.send(ApiRequest.of(HttpMethod.POST, "contacts/bulk-delete/")
                .json(BulkContactDeleteRequest.builder().contactIds(contactIds.stream().map(String::strip).toList()).build()),
                BulkContactDeleteResult.class);
    }

    /** {@code GET /api/v1/contacts/{id}/activity/}: email and delivery timeline. */
    public List<ContactActivity> activity(String contactId) {
        return http.sendList(ApiRequest.of(HttpMethod.GET, "contacts/{}/activity/", Validate.nonBlank(contactId, "contactId")),
                ContactActivity.class);
    }

    /** {@code GET /api/v1/contacts/sample-template/}: the CSV template for bulk uploads. */
    public String sampleTemplate() {
        return http.sendText(ApiRequest.of(HttpMethod.GET, "contacts/sample-template/"));
    }

    /** {@code POST /api/v1/contacts/bulk-upload/}: imports contacts from a CSV file (sent as {@code text/csv}). */
    public BulkContactUploadResult bulkUpload(FileUpload csv) {
        return http.send(ApiRequest.of(HttpMethod.POST, "contacts/bulk-upload/")
                .multipart(Map.of(), csv.withContentType("text/csv")), BulkContactUploadResult.class);
    }

    /** Audience groups (lists). */
    public static final class GroupsApi {
        private final HttpTransport http;

        GroupsApi(HttpTransport http) {
            this.http = http;
        }

        /** {@code GET /api/v1/contacts/groups/}. */
        public Page<ContactGroup> list(Query query) {
            return http.listPage("contacts/groups/", query, ContactGroup.class);
        }

        /** {@code GET /api/v1/contacts/groups/{id}/}. */
        public ContactGroup get(String groupId) {
            return http.send(ApiRequest.of(HttpMethod.GET, "contacts/groups/{}/", Validate.nonBlank(groupId, "groupId")),
                    ContactGroup.class);
        }

        /** {@code POST /api/v1/contacts/groups/}. */
        public ContactGroup create(ContactGroupRequest request) {
            return http.send(ApiRequest.of(HttpMethod.POST, "contacts/groups/").json(request), ContactGroup.class);
        }

        /** {@code PATCH /api/v1/contacts/groups/{id}/}. */
        public ContactGroup update(String groupId, PatchedContactGroupRequest request) {
            return http.send(ApiRequest.of(HttpMethod.PATCH, "contacts/groups/{}/", Validate.nonBlank(groupId, "groupId"))
                    .json(request), ContactGroup.class);
        }

        /** {@code DELETE /api/v1/contacts/groups/{id}/}. */
        public void delete(String groupId) {
            http.send(ApiRequest.of(HttpMethod.DELETE, "contacts/groups/{}/", Validate.nonBlank(groupId, "groupId")));
        }
    }
}
