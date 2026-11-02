# Reading the committed Generalized Notation Notation document.
#
# This file is dependency free on purpose. `src/ActInf_RxInfer.jl` includes it
# so the implementation is built from the declarations in
# `specs/coin_flip.gnn.md`, and `scripts/validate_gnn_spec.py` runs it with a
# bare `julia` binary to compare the declared parameters across the pinned GNN
# parser, the Python reader, and this reader. Do not add `using` statements.

"""
    GNNSpecParameters

Parameters of the Beta-Bernoulli coin-flip model declared by
`specs/coin_flip.gnn.md`.
"""
struct GNNSpecParameters
    prior_a::Float64
    prior_b::Float64
    theta_true::Float64
    n_observations::Int
    seed::Int
end

"""Absolute path of the committed GNN document."""
const SPEC_PATH = joinpath(dirname(@__DIR__), "specs", "coin_flip.gnn.md")

"""Declarations of the `InitialParameterization` section read by this reader."""
const SPEC_SCALAR_KEYS = ("a", "b", "theta_true", "n_observations", "seed")

"""
    spec_section(path, name) -> String

Return the body of the `## name` section of the GNN document at `path`.
"""
function spec_section(path::AbstractString, name::AbstractString)::String
    text = read(path, String)
    header = match(Regex("(?m)^##[ \\t]*" * name * "[ \\t]*\$"), text)
    header === nothing && throw(ArgumentError("section '## $name' not found in $path"))
    tail = header.offset + ncodeunits(header.match)
    tail > ncodeunits(text) && return ""
    body = SubString(text, nextind(text, tail))
    following = findfirst(Regex("(?m)^##[ \\t]+[^ \\t]"), body)
    following === nothing && return String(body)
    first(following) == 1 && return ""
    return String(SubString(body, 1, first(following) - 1))
end

"""
    spec_scalar(path, key) -> Float64

Return the number declared for `key` in the `InitialParameterization` section.
"""
function spec_scalar(path::AbstractString, key::AbstractString)::Float64
    section = spec_section(path, "InitialParameterization")
    pattern = Regex("(?m)^[ \\t]*" * key * "[ \\t]*=[ \\t]*\\{[ \\t]*\\(([^)]*)\\)[ \\t]*\\}")
    found = match(pattern, section)
    found === nothing && throw(
        ArgumentError("scalar '$key' is not declared in InitialParameterization of $path")
    )
    value = tryparse(Float64, strip(found.captures[1]))
    value === nothing && throw(
        ArgumentError("declared value for '$key' in $path is not a number: $(found.captures[1])")
    )
    return value
end

"""
    spec_model_name(path = SPEC_PATH) -> String

Return the model name declared by the GNN document.
"""
function spec_model_name(path::AbstractString = SPEC_PATH)::String
    return strip(spec_section(path, "ModelName"))
end

"""
    spec_parameters(path = SPEC_PATH) -> GNNSpecParameters

Read the coin-flip model parameters declared by the GNN document.
"""
function spec_parameters(path::AbstractString = SPEC_PATH)::GNNSpecParameters
    values = Dict(key => spec_scalar(path, key) for key in SPEC_SCALAR_KEYS)
    return GNNSpecParameters(
        values["a"],
        values["b"],
        values["theta_true"],
        Int(round(values["n_observations"])),
        Int(round(values["seed"])),
    )
end

"""
    spec_summary(path = SPEC_PATH) -> String

Return `key=value` lines describing the declared model, the form consumed by
`scripts/validate_gnn_spec.py`.
"""
function spec_summary(path::AbstractString = SPEC_PATH)::String
    parameters = spec_parameters(path)
    return join(
        (
            "model_name=" * spec_model_name(path),
            "prior_a=$(parameters.prior_a)",
            "prior_b=$(parameters.prior_b)",
            "theta_true=$(parameters.theta_true)",
            "n_observations=$(parameters.n_observations)",
            "seed=$(parameters.seed)",
        ),
        "\n",
    )
end
