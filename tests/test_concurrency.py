"""FR-3: concurrent requests never corrupt balances (real threads, one client per thread)."""
from concurrent.futures import ThreadPoolExecutor
from collections import Counter

from fastapi.testclient import TestClient

from tests.helpers import balance, deposit, key, make_wallet, reconcile, scalar, transfer


def run_parallel(app, jobs, workers=20):
    def call(job):
        return job(TestClient(app))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(call, jobs))


def test_only_one_of_many_competing_transfers_succeeds(client, app):
    a, b = make_wallet(client), make_wallet(client)
    deposit(client, a, 100)
    results = run_parallel(app, [lambda c: transfer(c, a, b, 100).status_code] * 20)
    assert Counter(results) == {201: 1, 422: 19}
    assert (balance(client, a), balance(client, b)) == (0, 100)
    assert reconcile(client)["status"] == "PASS"


def test_many_concurrent_transfers_all_apply_exactly(client, app):
    a, b = make_wallet(client), make_wallet(client)
    deposit(client, a, 1000)
    results = run_parallel(app, [lambda c: transfer(c, a, b, 10).status_code] * 100)
    assert Counter(results) == {201: 100}
    assert (balance(client, a), balance(client, b)) == (0, 1000)
    assert reconcile(client)["status"] == "PASS"


def test_same_key_concurrently_executes_exactly_once(client, app):
    a, b = make_wallet(client), make_wallet(client)
    deposit(client, a, 1000)
    h = key()
    responses = run_parallel(app, [lambda c: transfer(c, a, b, 100, headers=h)] * 10)
    assert {r.status_code for r in responses} == {201}
    assert sum(1 for r in responses if "Idempotent-Replayed" not in r.headers) == 1
    assert scalar(app, "select count(*) from ledger_transactions where type='transfer'") == 1
    assert balance(client, b) == 100


def test_opposite_direction_transfers_do_not_deadlock(client, app):
    a, b = make_wallet(client), make_wallet(client)
    deposit(client, a, 500)
    deposit(client, b, 500)
    jobs = [(lambda c: transfer(c, a, b, 5).status_code) if i % 2 else (lambda c: transfer(c, b, a, 5).status_code) for i in range(40)]
    assert set(run_parallel(app, jobs)) == {201}
    assert balance(client, a) + balance(client, b) == 1000
    assert reconcile(client)["status"] == "PASS"
