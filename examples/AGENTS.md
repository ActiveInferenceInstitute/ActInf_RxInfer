# AGENTS.md — `examples/`

- Do not hardcode the prior, observation count or seed; read them with
  `spec_parameters`. The specification is the single source of truth.
- Keep the script runnable with `julia --project=.` from the repository root.
- A change in recorded output belongs in the same change as the root
  `README.md` and `docs/getting_started.md` updates.
- Parent rules: [../AGENTS.md](../AGENTS.md).
