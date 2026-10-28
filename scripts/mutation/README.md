# Mutation testing

Mutation testing asks whether the tests *notice* wrong code: a tool makes small changes (flip a comparison, drop an
argument, change a constant) and re-runs the tests; a mutant that no test fails on has **survived**.
Scores are evidence, not proof: some survivors are equivalent (for example a changed log message) and a high score does
not mean the right behaviours are pinned down. Read the survivors, not the percentage.

| SDK | Tool | Script | Scope (handwritten transport code only) |
|---|---|---|---|
| Python | mutmut 3 | `run_python.sh` | `http.py`, `config.py`, `pagination.py`, `exceptions.py` |
| TypeScript | StrykerJS 10 (needs Node 22+) | `run_typescript.sh` | `http.ts`, `config.ts`, `errors.ts`, `models.ts` |
| Java | PIT 1.30 (Maven profile `mutation`) | `run_java.sh` | `http.*`, `NovaConfig`, `Page*`, `Query*`, `errors.*`, `Validate` |

Each script works on a scratch copy (Python, TypeScript) or in `target/` (Java), never edits tracked files, and prints
where the report is. Runs take roughly 5-20 minutes each. They are deliberately **not** part of ordinary CI.

Generated models (`schemas.py`, `schemas.ts`, `models/`) are excluded: they are reproducible from the OpenAPI contract and
checked by `gen_*.py --check`.
