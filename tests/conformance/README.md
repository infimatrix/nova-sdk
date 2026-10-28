# Cross-language conformance suite

One neutral scenario file, one real local HTTP server, and a thin driver per language. The same 100+ scenarios run
against the Python, TypeScript and Java SDKs; a scenario passes only if the SDK produced the **documented** requests and
outcome.

```bash
# prerequisites: pip install -e sdks/python httpx pyyaml; (cd sdks/typescript && npm ci && npm run build);
#                (cd sdks/java && mvn -DskipTests compile)
python tests/conformance/conformance.py                  # all three SDKs
python tests/conformance/conformance.py --sdk python --only C-13   # one SDK, scenarios whose id contains C-13
pytest tests/conformance                                  # tests of the checker itself (no SDK needed)
python tests/conformance/inject_defects.py --python-env <python with httpx, without nova_sdk>   # local: injects bugs
```

## Why it is built this way

* **Expectations are independent of the SDKs.** Every scenario carries a `doc` field naming the documented rule it comes
  from (`docs/conventions.md`, `error-handling.md`, `authentication.md`, HTTP/RFC semantics). Nothing is generated from
  SDK code or from recorded SDK output. Where the docs are silent the scenario does not exist
  ([verification plan, Gaps](../../docs/verification-plan.md#gaps)).
* **Real sockets.** The server records exactly what arrived (method, raw path, raw query, headers, body, arrival time),
  so request-shape bugs cannot hide behind a mocked HTTP layer, and retry delays are measured, not assumed.
* **Neutral outcomes.** Drivers map each SDK's error classes to one vocabulary (`Validation`, `NotFound`, `RateLimit`, ...)
  so the same expectation applies to all three.
* **The checker is tested.** `test_checker.py` feeds the checker wrong observations (wrong header, extra retry, leaked
  secret, hostile path ...) and requires a violation for each. `inject_defects.py` goes one step further: it plants
  representative bugs in copies of each SDK and requires the suite to fail.
* **Hostile path ids** are judged by an invariant, not by an exact URL: the SDK may either reject the id before sending
  or send exactly one encoded, non-dot segment that decodes back to the id.

## Scenario format

```jsonc
{ "id": "C-09-get-retried-on-503", "doc": "error-handling: ...",
  "client": { "api_key": "...", "max_retries": 3 },          // SDK-neutral options
  "call":   { "op": "templates.get", "id": "t-1" },          // abstract operation
  "server": [ {"status": 503, "json": {...}}, {"status": 200, "json": {...}} ],   // script, last step repeats
  "expect": { "request_count": 2, "outcome": {"kind": "ok", "data": {...}} },
  "variants": [ {"server.0.status": 502}, ... ] }            // dotted-path overrides expand into separate runs
```

Not covered here (see the verification report): the live Nova backend, TLS verification, the 30 s `Retry-After` cap
(too slow; covered by unit tests), cancellation, multipart uploads.
