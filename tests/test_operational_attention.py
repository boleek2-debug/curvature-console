from curvature_console.infrastructure.operational_attention import (
    OperationalAttentionKind,
    classify_operational_attention,
    status_for_attention,
)


def test_explicit_operator_decision_wins() -> None:
    attention = classify_operational_attention(
        "workflow_state: AWAITING_OPERATOR_DECISION\nApproval needed."
    )
    assert attention.kind is OperationalAttentionKind.OPERATOR_DECISION
    assert status_for_attention(attention) == "AWAITING_OPERATOR_DECISION"


def test_blocker_is_classified() -> None:
    attention = classify_operational_attention(
        "Cannot proceed because the required route is unavailable."
    )
    assert attention.kind is OperationalAttentionKind.BLOCKER
    assert status_for_attention(attention) == "BLOCKED"


def test_normal_completion_is_result() -> None:
    attention = classify_operational_attention("Validation complete: 251 passed.")
    assert attention.kind is OperationalAttentionKind.RESULT
    assert status_for_attention(attention) == "RESULT_READY"
