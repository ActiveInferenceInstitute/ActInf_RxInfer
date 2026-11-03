# `test/`

[`runtests.jl`](runtests.jl) is the package test suite: it checks the GNN
declaration and its reader, rejects incomplete documents, and verifies the
message-passing posterior against the closed-form conjugate posterior.

Run: `julia --project=. -e 'using Pkg; Pkg.test()'`. CI runs the same suite on
Julia 1.10 and on stable.
