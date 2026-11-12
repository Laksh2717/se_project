"""FR-1, FR-2, FR-4, FR-5 happy paths and the accounting invariants."""
from tests.helpers import balance, deposit, make_wallet, reconcile, reverse, scalar, transfer


def test_new_wallet_starts_at_zero(client):
    assert balance(client, make_wallet(client)) == 0


def test_deposit_writes_balanced_pair_against_funding_wallet(client, app):
    w = make_wallet(client)
    r = deposit(client, w, 1000)
    assert r.status_code == 201 and r.json()["balance_minor"] == 1000
    assert scalar(app, "select count(*) from ledger_entries") == 2
    assert scalar(app, "select balance_minor from wallets where is_system=1 and currency='USD'") == -1000
    assert scalar(app, "select sum(balance_minor) from wallets where currency='USD'") == 0
    assert reconcile(client)["status"] == "PASS"


def test_transfer_moves_money_and_reconciles(client, app):
    a, b = make_wallet(client), make_wallet(client)
    deposit(client, a, 1000)
    r = transfer(client, a, b, 400)
    assert r.status_code == 201
    assert (balance(client, a), balance(client, b)) == (600, 400)
    details = client.get(f"/v1/transfers/{r.json()['transaction_id']}").json()
    assert [e["direction"] for e in details["entries"]] == ["DEBIT", "CREDIT"]
    assert reconcile(client)["status"] == "PASS"


def test_entries_endpoint_is_ascending(client):
    a, b = make_wallet(client), make_wallet(client)
    deposit(client, a, 500)
    transfer(client, a, b, 100)
    seqs = [e["seq"] for e in client.get(f"/v1/wallets/{a}/entries").json()["items"]]
    assert seqs == sorted(seqs) and len(seqs) == 2


def test_insufficient_funds_changes_nothing(client, app):
    a, b = make_wallet(client), make_wallet(client)
    deposit(client, a, 50)
    r = transfer(client, a, b, 100)
    assert r.status_code == 422 and r.json()["error"]["code"] == "INSUFFICIENT_FUNDS"
    assert balance(client, a) == 50 and scalar(app, "select count(*) from ledger_entries") == 2
    assert scalar(app, "select count(*) from idempotency_keys") == 1  # only the deposit's key


def test_reversal_mirrors_entries_and_reconciles(client):
    a, b = make_wallet(client), make_wallet(client)
    deposit(client, a, 1000)
    t = transfer(client, a, b, 300).json()["transaction_id"]
    r = reverse(client, t)
    assert r.status_code == 201 and r.json()["reverses_transaction_id"] == t
    assert (balance(client, a), balance(client, b)) == (1000, 0)
    assert reconcile(client)["status"] == "PASS"


def test_second_reversal_is_409_even_when_funds_exist(client):
    a, b = make_wallet(client), make_wallet(client)
    deposit(client, a, 1000)
    t = transfer(client, a, b, 300).json()["transaction_id"]
    assert reverse(client, t).status_code == 201
    deposit(client, b, 300)  # destination could afford a second reversal
    assert reverse(client, t).status_code == 409


def test_reversal_of_a_reversal_is_409(client):
    a, b = make_wallet(client), make_wallet(client)
    deposit(client, a, 100)
    t = transfer(client, a, b, 100).json()["transaction_id"]
    rev = reverse(client, t).json()["transaction_id"]
    assert reverse(client, rev).status_code == 409


def test_reversal_that_would_overdraw_is_422(client):
    a, b, c = make_wallet(client), make_wallet(client), make_wallet(client)
    deposit(client, a, 100)
    t = transfer(client, a, b, 100).json()["transaction_id"]
    transfer(client, b, c, 100)
    r = reverse(client, t)
    assert r.status_code == 422 and r.json()["error"]["code"] == "INSUFFICIENT_FUNDS"
    assert reconcile(client)["status"] == "PASS"


def test_deposit_can_be_reversed(client):
    a = make_wallet(client)
    d = deposit(client, a, 250).json()["transaction_id"]
    assert reverse(client, d).status_code == 201
    assert balance(client, a) == 0 and reconcile(client)["status"] == "PASS"


def test_reverse_unknown_transaction_is_404(client):
    assert reverse(client, "00000000-0000-4000-8000-000000000000").status_code == 404


def test_get_unknown_transfer_is_404(client):
    assert client.get("/v1/transfers/00000000-0000-4000-8000-000000000000").status_code == 404


def test_precision_1000_transfers_of_one_minor_unit(client):
    a, b = make_wallet(client), make_wallet(client)
    deposit(client, a, 1000)
    for _ in range(1000):
        assert transfer(client, a, b, 1).status_code == 201
    assert (balance(client, a), balance(client, b)) == (0, 1000)
    assert reconcile(client)["status"] == "PASS"
