#!/usr/bin/env bash
# PIT on the handwritten Java transport (Maven profile "mutation" in sdks/java/pom.xml). Usage: scripts/mutation/run_java.sh
set -euo pipefail
root="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$root/sdks/java"
mvn -B -ntp -Pmutation test-compile org.pitest:pitest-maven:mutationCoverage
echo "report: $root/sdks/java/target/pit-reports/index.html (mutations.xml for machine-readable results)"
