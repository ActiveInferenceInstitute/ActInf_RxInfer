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

The Python side of the gate has no test file here: the pin's shape is checked by
the shared `gnn.importers` reader, which `./run.sh gnn` runs from the pinned
revision.
