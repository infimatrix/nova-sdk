// AUTO-GENERATED from openapi/nova-api.yaml by scripts/gen_java_models.py.
// Do not edit by hand; run the script to regenerate.

package com.infimatrix.nova.models;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.List;

/**
 * DashboardAnalytics model.
 *
 * @param totalContacts JSON property total_contacts.
 * @param newContacts JSON property new_contacts.
 * @param emailOverview JSON property email_overview.
 * @param recentlyAddedContacts JSON property recently_added_contacts.
 * @param recentlyFailedMessages JSON property recently_failed_messages.
 */
@JsonIgnoreProperties(ignoreUnknown = true)
@JsonInclude(JsonInclude.Include.NON_NULL)
public record DashboardAnalytics(
    @JsonProperty("total_contacts") Long totalContacts,
    @JsonProperty("new_contacts") Long newContacts,
    @JsonProperty("email_overview") EmailOverview emailOverview,
    @JsonProperty("recently_added_contacts") List<ContactSummary> recentlyAddedContacts,
    @JsonProperty("recently_failed_messages") List<RecentFailedMessage> recentlyFailedMessages
) {
}
