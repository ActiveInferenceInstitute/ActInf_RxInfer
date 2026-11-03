# AGENTS.md — `scripts/`

- Never import the upstream `gnn` package outside `gnn_parser_probe.py`; the
  probe runs in a subprocess with the pinned tree first on `PYTHONPATH`.
- Keep the exit codes: `0` pass, `2` not run. A missing runtime must not report
  success.
- Verify the parser file digests in `specs/gnn-pin.json` before using a parsed
  result.
- A model change updates the specification first, then this validator's
  expectations, in the same change.
- Parent rules: [../AGENTS.md](../AGENTS.md).
