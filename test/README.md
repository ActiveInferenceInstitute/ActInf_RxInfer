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

[`test_gnn_pin.py`](test_gnn_pin.py) checks the local Python pin reader against
the committed pin and rejects missing or malformed schemas. `./run.sh gnn`
runs these standard-library unit tests before resolving the pinned parser.
