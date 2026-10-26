# Nova SDKs

Official client libraries for the **Nova** email template and delivery platform.

| Language | Directory | Package |
|---|---|---|
| Python 3.10+ (sync + async) | [sdks/python](sdks/python) | `infimatrix-nova-sdk` |
| TypeScript / Node.js 18.17+ | [sdks/typescript](sdks/typescript) | `@infimatrix/nova-sdk` |
| Java 17+ | [sdks/java](sdks/java) | `com.infimatrix:nova-sdk` |

Kotlin/Android and Go are not implemented. **None of the packages has been published yet**; see
[docs/distribution.md](docs/distribution.md).

All three SDKs implement the same 98 required API operations (102 in the contract minus 4 documented exclusions in
[openapi/sdk-exclusions.yaml](openapi/sdk-exclusions.yaml)), measured by `scripts/check_sdk_coverage.py`.

The SDKs are built from a committed OpenAPI snapshot ([openapi/nova-api.yaml](openapi/nova-api.yaml)) of the Nova
REST API. This repository does not contain the backend. See [docs/](docs/README.md) for getting started,
authentication, error handling, conventions, versioning, and how to [update the contract](docs/openapi-sync.md).

## Development

```bash
pip install -r requirements-dev.txt
pytest                                          # contract snapshot + SDK alignment checks
python scripts/check_sdk_coverage.py --strict   # every SDK implements every required operation
python scripts/gen_python_models.py --check && python scripts/gen_python_async.py --check \
  && python scripts/gen_ts_types.py --check && python scripts/gen_java_models.py --check

cd sdks/python && pip install -e ".[dev]" && pytest
cd sdks/typescript && npm ci && npm run typecheck && npm test && npm run build
cd sdks/java && mvn verify        # JDK 17+, Maven 3.9+
```

Packages are distributed only through Google Cloud Artifact Registry. No release has been made and no registry resources
are configured by this repository.

| I want to… | Read |
|---|---|
| Publish the SDKs to Artifact Registry | [docs/deploy-artifact-registry.md](docs/deploy-artifact-registry.md) |
| Install and use the Python SDK | [docs/using-python.md](docs/using-python.md) |
| Install and use the Node.js SDK | [docs/using-node.md](docs/using-node.md) |
| Install and use the Java SDK | [docs/using-java.md](docs/using-java.md) |
| Understand the safeguards and release process | [docs/distribution.md](docs/distribution.md), [docs/releasing.md](docs/releasing.md) |

Release workflows exist for Python (`python-v*` tags) and TypeScript (`typescript-v*` tags). Java is published manually
until a workflow is added.

## License

MIT. See [LICENSE](LICENSE); every SDK package (`sdks/*/LICENSE`, `pyproject.toml`, `package.json`, `pom.xml`) declares the same license.
