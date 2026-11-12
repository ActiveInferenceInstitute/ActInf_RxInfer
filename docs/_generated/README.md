# `docs/_generated/`

Machine-owned measurement records. Every file here is written by a script and
checked by the `docs` arm, so a hand edit is a test failure rather than a silent
change.

| File | Producer | Refresh | Verify |
| --- | --- | --- | --- |
| `gate-receipt.json` | [`scripts/gate_report.py`](../../scripts/gate_report.py) | `./run.sh measure` | `./run.sh docs` |
| `gate.md` | [`scripts/gate_report.py`](../../scripts/gate_report.py) | `./run.sh measure` | `./run.sh docs` |

`gate.md` is rendered from `gate-receipt.json`; the receipt is the measurement.
The `docs` arm re-renders the table from the receipt and compares the result
with the committed file, so the numbers in the documentation always name the
host, the tool versions, and the commit they came from.

Measured numbers belong here, not in prose: link [`gate.md`](gate.md) and let
the script state the wall times.
