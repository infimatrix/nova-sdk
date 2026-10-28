"""Tests of the conformance checker itself: it must flag each kind of wrong behaviour and accept right behaviour.

A checker that accepts everything would make the cross-language run meaningless, so every rule has a case here that
must be reported.
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import conformance as c

SCENARIOS = {s["run_id"]: s for s in c.expand(json.loads((Path(__file__).parent / "scenarios.json").read_text(encoding="utf-8")))}


def req(method="GET", path="/api/v1/health/", headers=None, query=None, body=b""):
    return {"method": method, "raw_path": path, "raw_query": "", "query": query or [], "headers": headers or {}, "body": body}


def violations(run_id, outcome, recorded):
    return c.check_observation(SCENARIOS[run_id], outcome, recorded)


def test_every_scenario_has_an_expectation_and_a_source():
    for run_id, s in SCENARIOS.items():
        assert s["doc"], run_id
        assert "outcome" in s["expect"], run_id


def test_variants_expand_to_distinct_concrete_scenarios():
    ids = [s["run_id"] for s in SCENARIOS.values()]
    assert len(ids) == len(set(ids))
    assert SCENARIOS["C-13-status-to-error-class#8"]["server"][0]["status"] == 500
    assert SCENARIOS["C-13-status-to-error-class#8"]["expect"]["outcome"]["category"] == "Server"
    # the base scenario must not be mutated by expansion
    base = json.loads((Path(__file__).parent / "scenarios.json").read_text(encoding="utf-8"))
    assert next(s for s in base if s["id"] == "C-13-status-to-error-class")["server"][0]["status"] == 400


GOOD_HEADERS = {
    "authorization": "Bearer nova_key_abc",
    "accept": "application/json",
    "x-tenant-id": "00000000-0000-0000-0000-000000000001",
    "user-agent": "Nova-Python-SDK/0.2.0",
}


def test_accepts_correct_headers_and_outcome():
    assert violations("C-01a-standard-headers", {"kind": "ok", "data": {"status": "ok"}}, [req(headers=GOOD_HEADERS)]) == []


@pytest.mark.parametrize(
    "mutation",
    [
        {"authorization": "nova_key_abc"},
        {"authorization": "Bearer Bearer nova_key_abc"},
        {"accept": "*/*"},
        {"x-tenant-id": "other"},
        {"user-agent": "python-httpx/0.28"},
    ],
)
def test_flags_each_wrong_header(mutation):
    headers = {**GOOD_HEADERS, **mutation}
    assert violations("C-01a-standard-headers", {"kind": "ok", "data": {"status": "ok"}}, [req(headers=headers)])


def test_flags_wrong_method_path_and_count():
    ok = {"kind": "ok", "data": {"status": "ok"}}
    assert violations("C-01a-standard-headers", ok, [req(method="POST", headers=GOOD_HEADERS)])
    assert violations("C-01a-standard-headers", ok, [req(path="/api/v1/health", headers=GOOD_HEADERS)])
    assert violations("C-01a-standard-headers", ok, [])
    assert violations("C-01a-standard-headers", ok, [req(headers=GOOD_HEADERS)] * 2)


def test_flags_tenant_header_that_must_be_absent():
    r = req(headers={"authorization": "Bearer nova_key_abc", "x-tenant-id": "leak"})
    assert violations("C-01b-no-tenant-header", {"kind": "ok"}, [r])


def test_retry_rules_flag_wrong_request_counts():
    ok = {"kind": "ok", "data": {"id": "t-1", "name": "Welcome"}}
    two = [req(path="/api/v1/templates/t-1/")] * 2
    assert violations("C-09-get-retried-on-503#0", ok, two) == []
    assert violations("C-09-get-retried-on-503#0", ok, two[:1])  # not retried
    assert violations("C-09-get-retried-on-503#0", ok, two * 2)  # retried too often
    server_err = {"kind": "error", "category": "Server", "status": 503}
    assert violations("C-10b-delete-not-retried", server_err, [req(method="DELETE", path="/api/v1/templates/t-1/")]) == []
    assert violations("C-10b-delete-not-retried", server_err, [req(method="DELETE", path="/api/v1/templates/t-1/")] * 2)
    assert violations("C-11a-retry-exhaustion", server_err, [req(path="/api/v1/templates/t-1/")] * 3) == []
    assert violations("C-11a-retry-exhaustion", server_err, [req(path="/api/v1/templates/t-1/")] * 4)


def test_error_classification_is_checked():
    r = [req(method="POST", path="/api/v1/templates/")]
    assert violations("C-13-status-to-error-class#3", {"kind": "error", "category": "NotFound", "status": 404}, r) == []
    assert violations("C-13-status-to-error-class#3", {"kind": "error", "category": "API", "status": 404}, r)
    assert violations("C-13-status-to-error-class#3", {"kind": "error", "category": "NotFound", "status": 500}, r)
    assert violations("C-13-status-to-error-class#3", {"kind": "ok", "data": None}, r)


def test_secret_in_message_is_flagged():
    r = [req(path="/api/v1/templates/t-1/")]
    base = {"kind": "error", "category": "Authentication", "status": 401}
    assert violations("C-17-secret-not-in-error", {**base, "message": "Invalid credentials"}, r) == []
    assert violations("C-17-secret-not-in-error", {**base, "message": "bad key nova_key_TOPSECRET_9f8e7d"}, r)
    assert violations("C-17-secret-not-in-error", {**base, "message": "token tok_TOPSECRET_1a2b3c"}, r)


def test_malformed_body_success_is_flagged():
    r = [req(path="/api/v1/templates/t-1/")]
    assert violations("C-16a-malformed-success-body", {"kind": "ok", "data": "{not json"}, r)
    assert violations("C-16a-malformed-success-body", {"kind": "error", "category": "API", "status": 200}, r) == []


@pytest.mark.parametrize(
    "sent_segment,id_,expected_ok",
    [
        ("a%2Fb", "a/b", True),  # encoded: fine
        ("a/b", "a/b", False),  # extra segment
        ("..", "..", False),  # dot-segment
        ("a%3Fb%3Dc", "a?b=c", True),
        ("a%20b", "a b", True),
        ("wrong", "a b", False),  # does not round trip
    ],
)
def test_path_id_invariant(sent_segment, id_, expected_ok):
    scenario = copy.deepcopy(SCENARIOS["C-07a-hostile-path-id#0"])
    scenario["call"]["id"] = id_
    got = c.check_observation(scenario, {"kind": "ok"}, [req(path=f"/api/v1/templates/{sent_segment}/")])
    assert (got == []) is expected_ok, got


def test_path_id_query_injection_is_flagged():
    scenario = copy.deepcopy(SCENARIOS["C-07a-hostile-path-id#0"])
    r = req(path="/api/v1/templates/a/")
    r["raw_query"] = "b=c"
    assert c.check_observation(scenario, {"kind": "ok"}, [r])


def test_path_id_rejection_must_be_a_client_validation_error():
    scenario = SCENARIOS["C-07a-hostile-path-id#0"]
    assert c.check_observation(scenario, {"kind": "error", "category": "Validation"}, []) == []
    assert c.check_observation(scenario, {"kind": "ok"}, [])  # nothing sent but reported success
    assert c.check_observation(scenario, {"kind": "error", "category": "Connection"}, [])


def test_scripted_server_selects_by_query_then_sequence():
    steps = [{"status": 200, "json": {"a": 1}}, {"status": 201, "when_query": {"page": "2"}, "json": {"b": 2}}]
    with c.ScriptedServer(steps) as server:
        import urllib.request

        def get(path):
            with urllib.request.urlopen(f"http://127.0.0.1:{server.port}{path}") as r:
                return r.status

        assert get("/x") == 200
        assert get("/x?page=2") == 201
        assert get("/x?page=3") == 200
    assert [r["query"] for r in server.requests] == [[], [("page", "2")], [("page", "3")]]


def test_gap_checks_flag_timing_outside_the_window():
    scenario = SCENARIOS["C-11c-backoff-doubles"]
    err = {"kind": "error", "category": "Server", "status": 503}

    def timed(*offsets_ms):
        return [{**req(path="/api/v1/templates/t-1/"), "t": ms / 1000} for ms in offsets_ms]

    assert c.check_observation(scenario, err, timed(0, 100, 300, 700)) == []  # 100, 200, 400 ms
    assert c.check_observation(scenario, err, timed(0, 50, 250, 650))  # first wait too short (divided, not multiplied)
    assert c.check_observation(scenario, err, timed(0, 100, 200, 600))  # second wait did not double
    assert c.check_observation(scenario, err, timed(0, 100, 300, 600))  # linear 100, 200, 300 instead of doubling
    assert c.check_observation(scenario, err, timed(0, 2000, 2200, 2600))  # far too long


def test_retry_after_scenario_requires_the_header_to_be_waited_on():
    scenario = SCENARIOS["C-12c-retry-after-waits"]
    ok = {"kind": "ok", "data": {"id": "t-1", "name": "Welcome"}}
    two = lambda gap: [{**req(path="/api/v1/templates/t-1/"), "t": t} for t in (0.0, gap)]
    assert c.check_observation(scenario, ok, two(1.0)) == []
    assert c.check_observation(scenario, ok, two(0.01))  # header ignored
    assert c.check_observation(scenario, ok, two(0.001))  # header scaled wrongly


def test_boundary_statuses_are_in_the_scenarios():
    redirects = {s["server"][0]["status"] for rid, s in SCENARIOS.items() if rid.startswith("C-15-")}
    assert {300, 399} <= redirects
    successes = {s["server"][0]["status"] for rid, s in SCENARIOS.items() if rid.startswith("C-15b-")}
    assert {200, 299} <= successes
