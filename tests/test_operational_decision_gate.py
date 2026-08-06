from curvature_console.infrastructure.operational_attention import (
    OperationalAttentionKind,
    classify_operational_attention,
)
from curvature_console.infrastructure.operational_decision_gate import (
    DecisionGateDomain,
    evaluate_operational_request_gate,
    render_operator_decision_stop,
)
from curvature_console.infrastructure.operational_request import OperationalRequest


def _request(task: str) -> OperationalRequest:
    return OperationalRequest(
        target_department_id="core",
        title="Decision gate test",
        task=task,
        relevant_context="Controlled test.",
        expected_output="Return a bounded result.",
        constraints=(),
        acceptance_criteria=("Return a result.",),
    )


def test_routine_collaboration_does_not_require_operator() -> None:
    assert evaluate_operational_request_gate(
        _request("Review the existing schema and report validation findings.")
    ) is None


def test_product_direction_requires_operator() -> None:
    gate = evaluate_operational_request_gate(
        _request("Make a product direction and roadmap decision for Chronicle.")
    )
    assert gate is not None
    assert gate.domain is DecisionGateDomain.PRODUCT_DIRECTION
    assert gate.question
    assert len(gate.options) >= 2
    assert len(gate.consequences) >= 2



def test_visual_identity_change_requires_operator() -> None:
    request = OperationalRequest(
        target_department_id="research",
        title="Choose Chronicle visual direction",
        task=(
            "Decide whether Curvature Chronicle should abandon the ASCII+ identity "
            "and use conventional rendered graphics instead."
        ),
        relevant_context="Controlled product-direction decision test.",
        expected_output="Recommend the final visual direction for Chronicle.",
        constraints=("Return one final recommendation.",),
        acceptance_criteria=("A single visual direction is selected.",),
    )
    gate = evaluate_operational_request_gate(request)
    assert gate is not None
    assert gate.domain is DecisionGateDomain.CANON_OR_ART

def test_repository_mutation_requires_operator() -> None:
    gate = evaluate_operational_request_gate(
        _request("Commit and push the completed implementation to origin/main.")
    )
    assert gate is not None
    assert gate.domain is DecisionGateDomain.REPOSITORY_MUTATION


def test_structured_gate_survives_attention_classification() -> None:
    gate = evaluate_operational_request_gate(
        _request("Install dependency with pip install before continuing.")
    )
    assert gate is not None
    rendered = render_operator_decision_stop(gate)
    attention = classify_operational_attention(rendered)
    assert attention.kind is OperationalAttentionKind.OPERATOR_DECISION
    assert attention.decision_question == gate.question
    assert attention.decision_options == gate.options
    assert attention.decision_consequences == gate.consequences
    assert gate.question in attention.reason
