# AGENTS.md — `src/`

- `spec_reader.jl` stays dependency free. Do not add `using`, `import` or a
  package call to it.
- Read the prior, observation count and seed from the specification; do not copy
  them into Julia constants.
- Public API changes update the export list, `test/runtests.jl`, the root
  `README.md` and `docs/` in the same change.
- Parent rules: [../AGENTS.md](../AGENTS.md).
