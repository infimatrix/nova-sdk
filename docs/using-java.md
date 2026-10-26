# Using the Java SDK

Artifact `com.infimatrix:nova-sdk`, Java 17+, one runtime dependency (`jackson-databind`). Reference:
[sdks/java/README.md](../sdks/java/README.md). Server-side only (not for Android apps).

> Publishing Java to Artifact Registry is a manual step today ([deploy guide](deploy-artifact-registry.md#3-java-maven)).
> Until a release exists, use the local install in section 4.

## 1. Authenticate to Artifact Registry

Needs `roles/artifactregistry.reader`. See the
[Maven authentication docs](https://docs.cloud.google.com/artifact-registry/docs/java/authentication).

`~/.m2/settings.xml` (do not commit; credentials stay out of the project):

```xml
<settings>
  <servers>
    <server>
      <id>artifact-registry</id>
      <username>oauth2accesstoken</username>
      <password>${env.AR_ACCESS_TOKEN}</password>   <!-- export AR_ACCESS_TOKEN="$(gcloud auth print-access-token)" -->
    </server>
  </servers>
</settings>
```

Alternatively use the `artifactregistry-maven-wagon` extension (credentials from `gcloud`/ADC); run
`gcloud artifacts print-settings mvn --repository=<REPOSITORY> --location=<LOCATION>` for the exact snippet.

## 2. Maven

```xml
<repositories>
  <repository>
    <id>artifact-registry</id>
    <url>https://<LOCATION>-maven.pkg.dev/<PROJECT>/<REPOSITORY></url>
  </repository>
</repositories>

<dependencies>
  <dependency>
    <groupId>com.infimatrix</groupId>
    <artifactId>nova-sdk</artifactId>
    <version>0.1.0</version>
  </dependency>
</dependencies>
```

## 3. Gradle

```kotlin
repositories {
    mavenCentral()
    maven {
        url = uri("https://<LOCATION>-maven.pkg.dev/<PROJECT>/<REPOSITORY>")
        credentials {
            username = "oauth2accesstoken"
            password = System.getenv("AR_ACCESS_TOKEN")
        }
    }
}
dependencies { implementation("com.infimatrix:nova-sdk:0.1.0") }
```

## 4. Local install (no registry)

```bash
cd sdks/java && mvn install     # into ~/.m2 only
```

## 5. Use

```java
import com.infimatrix.nova.NovaClient;
import com.infimatrix.nova.models.SendEmailRequest;

NovaClient nova = NovaClient.builder().build();   // reads NOVA_BASE_URL, NOVA_API_KEY, NOVA_TENANT_ID
var email = nova.emails().send(SendEmailRequest.builder()
        .recipientEmail("ada@example.com").subject("Welcome!").htmlContent("<h1>Hi</h1>").build());
System.out.println(email.messageId() + " " + email.status());
```

Exceptions are unchecked and extend `NovaException`; see [error handling](error-handling.md) and
[authentication](authentication.md).
