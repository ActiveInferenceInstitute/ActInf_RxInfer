# AGENTS.md — `scripts/`

- Never import the upstream `gnn` package into this repository's own
  interpreter. `gnn_parser_probe.py` runs in a subprocess of the pinned
  runtime, and the validator reads the pin the same way, through
  `gnn.importers.read_pin`; keep both in that runtime.
- Keep the exit codes: `0` pass, `2` not run. A missing runtime must not report
  success.
- Verify the parser file digests in `specs/gnn-pin.json` before using a parsed
  result.
- A model change updates the specification first, then this validator's
  expectations, in the same change.
- Parent rules: [../AGENTS.md](../AGENTS.md).
