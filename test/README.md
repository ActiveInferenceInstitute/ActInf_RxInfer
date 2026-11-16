# `test/`

[`runtests.jl`](runtests.jl) is the package test suite: it checks the GNN
declaration and its reader, rejects incomplete documents, generates the declared
data reproducibly, and verifies the message-passing posterior against the
closed-form conjugate posterior.

Two arms select the work through `ACTINF_RXINFER_TEST_ARM`:

- `./run.sh fast` sets `fast`: the two testsets that start RxInfer message
  passing are reported as deferred.
- `./run.sh full` runs every testset through `Pkg.test()`; CI runs this arm on
  Julia 1.10 and on stable.

Neither arm is a separate file. `docs/gate.md` documents both, and
`examples/coin_flip.jl` is exercised by the last testset of the full arm.

The producer owns pin normalization; consumer tests do not restore a second
pin parser. [`test_validate_gnn_spec.py`](test_validate_gnn_spec.py) retains
tag/URL/language contracts, including a real disposable offline tag store and
stubbed remote transport.

[`test_gnn_verification_order.py`](test_gnn_verification_order.py) requires
both independently reviewed resources, an explicitly selected parser runtime
with its dependencies, and actual producer files. It copies these into
disposable storage and exercises unchecked execution, bytecode, manifest/member
corruption, guarded lifetimes, origin and runtime-selection failures with real
processes. Missing prerequisites fail setup, not skip-as-pass. Positive cases
parse/check the committed specification with actual producer code, not stand-in
parsers or fabricated installation metadata.

[`test_run_gate.py`](test_run_gate.py) remains isolated dispatch/cache evidence,
not parser, Julia or installed-runtime qualification. The GNN gate supplies its
selected runtime to regression children.
