#!/usr/bin/env bash
# Consumes the SDK like an external application: resolves com.infimatrix:nova-sdk from a Maven
# repository that already contains it (installed locally; nothing is published), compiles a small
# program against the public API only, and runs it against a local JDK HTTP server.
#
# Usage: sdks/java/scripts/smoke-test.sh [LOCAL_MAVEN_REPO]
set -euo pipefail

REPO="${1:-$HOME/.m2/repository}"
VERSION="$(sed -n 's:.*<version>\(.*\)</version>.*:\1:p' "$(dirname "$0")/../pom.xml" | head -1)"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

cat > "$WORK/pom.xml" <<POM
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>example</groupId><artifactId>consumer</artifactId><version>1</version>
  <dependencies>
    <dependency><groupId>com.infimatrix</groupId><artifactId>nova-sdk</artifactId><version>${VERSION}</version></dependency>
  </dependencies>
</project>
POM

(cd "$WORK" && mvn -B -ntp -q -Dmaven.repo.local="$REPO" \
  org.apache.maven.plugins:maven-dependency-plugin:3.8.1:build-classpath -Dmdep.outputFile=cp.txt)

cat > "$WORK/Smoke.java" <<'JAVA'
import com.infimatrix.nova.FileUpload;
import com.infimatrix.nova.NovaClient;
import com.infimatrix.nova.Page;
import com.infimatrix.nova.Query;
import com.infimatrix.nova.errors.NovaNotFoundException;
import com.infimatrix.nova.models.Template;
import com.sun.net.httpserver.HttpServer;
import java.net.InetAddress;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;

public class Smoke {
    public static void main(String[] args) throws Exception {
        HttpServer server = HttpServer.create(new InetSocketAddress(InetAddress.getLoopbackAddress(), 0), 0);
        server.createContext("/", exchange -> {
            String path = exchange.getRequestURI().getPath();
            boolean missing = path.endsWith("/missing/");
            String body = missing
                    ? "{\"success\":false,\"message\":\"gone\",\"error\":{\"code\":\"NOT_FOUND\",\"message\":\"gone\",\"details\":{}}}"
                    : path.endsWith("/templates/")
                            ? "{\"success\":true,\"message\":\"ok\",\"data\":{\"success\":true,\"pagination\":{\"count\":2,\"next\":null,"
                                    + "\"previous\":null,\"page\":1,\"total_pages\":1,\"page_size\":2},\"results\":["
                                    + "{\"id\":\"1\",\"name\":\"Welcome\"},{\"id\":\"2\",\"name\":\"Reset\"}]},\"meta\":{}}"
                            : "{\"success\":true,\"message\":\"ok\",\"data\":{\"status\":\"ok\",\"database\":\"healthy\"},\"meta\":{}}";
            byte[] bytes = body.getBytes(StandardCharsets.UTF_8);
            exchange.getResponseHeaders().add("Content-Type", "application/json");
            exchange.sendResponseHeaders(missing ? 404 : 200, bytes.length);
            exchange.getResponseBody().write(bytes);
            exchange.close();
        });
        server.start();
        try {
            NovaClient nova = NovaClient.builder()
                    .baseUrl("http://127.0.0.1:" + server.getAddress().getPort())
                    .apiKey("nova_key_smoke_test_1234567890")
                    .build();
            System.out.println("health: " + nova.health().status());
            Page<Template> page = nova.templates().list(Query.builder().pageSize(2).build());
            for (Template t : page) {
                System.out.println("template: " + t.name());
            }
            try {
                nova.templates().get("missing");
                throw new AssertionError("expected NovaNotFoundException");
            } catch (NovaNotFoundException e) {
                System.out.println("typed error: " + e.errorCode());
            }
            if (nova.toString().contains("smoke_test_1234567890")) {
                throw new AssertionError("secret leaked");
            }
            System.out.println("client: " + nova);
            FileUpload.of("x".getBytes(StandardCharsets.UTF_8), "x.txt");
        } finally {
            server.stop(0);
        }
    }
}
JAVA

CP="$(cat "$WORK/cp.txt")"
"${JAVA_HOME:+$JAVA_HOME/bin/}javac" -Xlint:all -cp "$CP" -d "$WORK/out" "$WORK/Smoke.java"
"${JAVA_HOME:+$JAVA_HOME/bin/}java" -cp "$WORK/out:$CP" Smoke
