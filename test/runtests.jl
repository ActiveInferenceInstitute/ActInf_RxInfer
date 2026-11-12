# Test suite for ActInf_RxInfer.
#
# The generative model is declared in specs/coin_flip.gnn.md, so these tests
# read the declarations from that document and check that the RxInfer message
# passing result agrees with the closed-form conjugate posterior.
#
# Two arms select the work: `ACTINF_RXINFER_TEST_ARM=fast` runs every testset
# that does not start RxInfer message passing, and `ACTINF_RXINFER_TEST_ARM=full`
# (the default) runs all of them. `./run.sh fast` and `./run.sh full` set the
# variable; CI runs the full arm.

using ActInf_RxInfer
using Distributions
using Random
using Test

const TEST_ARM = get(ENV, "ACTINF_RXINFER_TEST_ARM", "full")
const EXPENSIVE_TESTSETS = (
    "message passing reproduces the conjugate posterior",
    "example script runs against the committed specification",
)
const PARAMETERS = spec_parameters()

if !(TEST_ARM in ("fast", "full"))
    error("ACTINF_RXINFER_TEST_ARM must be `fast` or `full`, got $(repr(TEST_ARM))")
end

@testset "ActInf_RxInfer" begin
    @testset "GNN specification" begin
        @test SPEC_PATH == joinpath(dirname(@__DIR__), "specs", "coin_flip.gnn.md")
        @test isfile(SPEC_PATH)
        @test spec_model_name() == "ActInf_RxInfer Beta-Bernoulli Coin Flip"
        @test PARAMETERS.prior_a == 2.0
        @test PARAMETERS.prior_b == 2.0
        @test PARAMETERS.theta_true == 0.75
        @test PARAMETERS.n_observations == 500
        @test PARAMETERS.seed == 123
        @test occursin(
            "theta | y ~ Beta(a + k, b + n - k)",
            spec_section(SPEC_PATH, "Equations"),
        )
    end

    @testset "spec reader rejects incomplete documents" begin
        path = joinpath(mktempdir(), "incomplete.gnn.md")
        write(path, "# GNN Specification: incomplete\n\n## ModelName\n\nIncomplete\n")
        @test spec_model_name(path) == "Incomplete"
        @test_throws ArgumentError spec_section(path, "InitialParameterization")
        @test_throws ArgumentError spec_scalar(path, "a")
        @test_throws ArgumentError spec_parameters(path)
    end

    @testset "declared data generation is reproducible" begin
        Random.seed!(PARAMETERS.seed)
        y = coin_data(PARAMETERS.theta_true, PARAMETERS.n_observations)
        @test length(y) == PARAMETERS.n_observations
        @test sum(y) == 371  # recorded for the declared seed and bias
        Random.seed!(PARAMETERS.seed)
        @test coin_data(PARAMETERS.theta_true, PARAMETERS.n_observations) == y
        @test all(coin_data(PARAMETERS.theta_true, PARAMETERS.n_observations; rng = MersenneTwister(7)) .==
                  coin_data(PARAMETERS.theta_true, PARAMETERS.n_observations; rng = MersenneTwister(7)))
    end

    if TEST_ARM == "fast"
        @testset "deferred to the full arm" begin
            for name in EXPENSIVE_TESTSETS
                @test_skip name
            end
        end
    else
        @testset "message passing reproduces the conjugate posterior" begin
            Random.seed!(PARAMETERS.seed)
            y = coin_data(PARAMETERS.theta_true, PARAMETERS.n_observations)
            posterior = coin_posterior(y; a = PARAMETERS.prior_a, b = PARAMETERS.prior_b)
            reference = analytic_posterior(y; a = PARAMETERS.prior_a, b = PARAMETERS.prior_b)
            n = length(y)
            @test reference isa Beta
            @test mean(reference) ==
                  (PARAMETERS.prior_a + sum(y)) / (PARAMETERS.prior_a + PARAMETERS.prior_b + n)
            @test mean(posterior) ≈ mean(reference) atol = 1e-8
            @test std(posterior) ≈ std(reference) atol = 1e-8
            @test quantile(posterior, [0.025, 0.975]) ≈
                  quantile(reference, [0.025, 0.975]) atol = 1e-8
            @test quantile(reference, 0.025) <= PARAMETERS.theta_true <=
                  quantile(reference, 0.975)
        end

        @testset "example script runs against the committed specification" begin
            output = Pipe()
            redirect_stdout(output) do
                include(joinpath(dirname(@__DIR__), "examples", "coin_flip.jl"))
            end
            close(output.in)
            printed = read(output, String)
            @test occursin("Inferred mean:", printed)
            @test occursin("Conjugate mean:", printed)
            @test occursin("500 (371 successes)", printed)
        end
    end
end
