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
    assert len(gate.action_types) == len(gate.options)



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
    assert gate.action_types == ("APPROVE", "REJECT", "REQUEST_NON_MUTATING_PREVIEW")
    assert "no commit or push" in gate.options[2].casefold()


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


def test_implementation_plan_approval_is_intercepted_before_target_routing() -> None:
    request = OperationalRequest(
        target_department_id="core",
        title="Approve Chronicle implementation plan",
        task="Approve the proposed implementation plan for the next Chronicle development phase.",
        relevant_context="Controlled Project-source revise test.",
        expected_output="Return a plan-approval decision with an option to request revision.",
        constraints=("Do not begin implementation before operator resolution.",),
        acceptance_criteria=("The operator can request a revised plan.",),
    )
    gate = evaluate_operational_request_gate(request)
    assert gate is not None
    assert gate.domain is DecisionGateDomain.IMPLEMENTATION_PLAN_APPROVAL
    assert gate.action_types == ("APPROVE", "REJECT", "REVISE")
    assert gate.options[2] == "Request a revised implementation plan."


def test_routine_implementation_plan_preparation_does_not_gate() -> None:
    request = OperationalRequest(
        target_department_id="core",
        title="Prepare Chronicle implementation plan",
        task="Prepare an implementation plan for the next Chronicle development phase.",
        relevant_context="Routine planning task.",
        expected_output="Return a draft implementation plan.",
        constraints=(),
        acceptance_criteria=("The plan is ready for later review.",),
    )
    assert evaluate_operational_request_gate(request) is None

def test_revision_work_that_mentions_future_approval_is_not_gated() -> None:
    request = OperationalRequest(
        target_department_id="core",
        title="Revise Chronicle implementation plan",
        task=(
            "Revise the proposed implementation plan for the next Chronicle development "
            "phase and return the amended plan for Project review."
        ),
        relevant_context=(
            "The operator selected REVISE. The previous plan is not approved and "
            "implementation remains unauthorized until a revised plan is reviewed and approved."
        ),
        expected_output=(
            "Return a revised Chronicle implementation plan suitable for a new Project approval decision."
        ),
        constraints=("Do not begin implementation.",),
        acceptance_criteria=("The revised plan is ready for a new approval decision.",),
    )
    assert evaluate_operational_request_gate(request) is None


def test_explicit_approval_of_revised_implementation_plan_is_gated() -> None:
    request = OperationalRequest(
        target_department_id="core",
        title="Approve revised Chronicle implementation plan",
        task="Approve the revised implementation plan before implementation begins.",
        relevant_context="The plan has already been amended by Core.",
        expected_output="Return an approval decision.",
        constraints=("Do not begin implementation before operator resolution.",),
        acceptance_criteria=("The operator can approve or revise the plan.",),
    )
    gate = evaluate_operational_request_gate(request)
    assert gate is not None
    assert gate.domain is DecisionGateDomain.IMPLEMENTATION_PLAN_APPROVAL


def test_revision_work_preserving_product_direction_is_not_product_direction_gate() -> None:
    request = OperationalRequest(
        target_department_id="core",
        title="Revise Chronicle implementation plan",
        task=(
            "Revise the proposed implementation plan for the next Chronicle development "
            "phase and return the amended plan for Project review."
        ),
        relevant_context=(
            "The operator selected REVISE during the implementation-plan approval gate."
        ),
        expected_output="Return a revised implementation plan.",
        constraints=(
            "Preserve the existing approved Chronicle product direction unless the revision "
            "explicitly identifies a decision that requires Project arbitration.",
        ),
        acceptance_criteria=("The revised plan is ready for a new approval decision.",),
    )
    assert evaluate_operational_request_gate(request) is None


def test_explicit_product_direction_change_inside_revision_work_still_gates() -> None:
    request = OperationalRequest(
        target_department_id="core",
        title="Revise Chronicle implementation plan",
        task=(
            "Revise the implementation plan and make a product direction decision about "
            "the Chronicle client architecture."
        ),
        relevant_context="Controlled explicit direction-change test.",
        expected_output="Return the revised plan.",
        constraints=(),
        acceptance_criteria=("The direction decision is reflected in the plan.",),
    )
    gate = evaluate_operational_request_gate(request)
    assert gate is not None
    assert gate.domain is DecisionGateDomain.PRODUCT_DIRECTION
