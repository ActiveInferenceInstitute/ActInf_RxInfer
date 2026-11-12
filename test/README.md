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

The pin's shape is not tested here: the shared `gnn.importers` reader checks it,
and `./run.sh gnn` runs that reader from the pinned revision.
[`test_validate_gnn_spec.py`](test_validate_gnn_spec.py) covers the validator's
own failure modes offline with the standard library: the tag/commit binding
(`tag-commit-mismatch`, with a stubbed `git ls-remote`), the installed-revision
comparison, digest verification before the parser runs, a remote tag check that
cannot answer ending the run as *not run*, and the language-version match.
[`test_gnn_verification_order.py`](test_gnn_verification_order.py) covers the
two ordering properties end to end, against a stand-in `gnn` package on
`PYTHONPATH` instead of a provisioned runtime: `./run.sh gnn` verifies the
digests before the shared reader imports the parser and parses the document
with it, and the package the digests are verified against is the package the
probe imports even when the working directory holds a stand-in whose digests
match the pin. Both use the standard library, spawn real subprocesses, and need
no network. `./run.sh gnn` runs them after the reader.
