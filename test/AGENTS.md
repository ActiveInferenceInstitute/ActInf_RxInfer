# AGENTS.md — `test/`

- Tests read the committed specification; do not replace it with inline
  constants that can drift.
- A new public behavior needs a test that fails without the change.
- Keep the suite runnable with `Pkg.test()` on Julia 1.10 and stable; no
  machine-specific paths.
- Parent rules: [../AGENTS.md](../AGENTS.md).
