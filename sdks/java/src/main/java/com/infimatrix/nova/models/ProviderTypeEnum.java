// AUTO-GENERATED from openapi/nova-api.yaml by scripts/gen_java_models.py.
// Do not edit by hand; run the script to regenerate.

package com.infimatrix.nova.models;

/** Allowed values of {@code ProviderTypeEnum} (kept as strings for forward compatibility). */
public final class ProviderTypeEnum {
    /** The value {@code "SMTP"}. */
    public static final String SMTP = "SMTP";
    /** The value {@code "AWS_SES"}. */
    public static final String AWS_SES = "AWS_SES";
    /** The value {@code "SENDGRID"}. */
    public static final String SENDGRID = "SENDGRID";
    /** The value {@code "MAILGUN"}. */
    public static final String MAILGUN = "MAILGUN";
    /** The value {@code "POSTMARK"}. */
    public static final String POSTMARK = "POSTMARK";
    /** The value {@code "MOCK"}. */
    public static final String MOCK = "MOCK";

    private ProviderTypeEnum() {
    }
}
