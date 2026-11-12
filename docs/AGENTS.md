# AGENTS.md — `docs/`

- `index.md` is the hub. Every page here is linked from it in the same change
  that adds the page, and every long-lived page is also listed in
  `documentation-index.md`. `./run.sh docs` enforces both.
- Describe only checked-in behavior. Commands and recorded output must match a
  real run; label the GNN check as needing a pinned runtime.
- Measured numbers live in `_generated/gate.md`, which `./run.sh measure`
  writes. Never type a wall time, test count, or coverage number into prose;
  link the generated record.
- Keep `getting_started.md` consistent with `Project.toml` and the root
  `README.md`, `gnn.md` consistent with `specs/gnn-pin.json`, and `gate.md`
  consistent with `run.sh` and `.github/workflows/ci.yml`.
- Parent rules: [../AGENTS.md](../AGENTS.md).
