"""Authority- and consequence-based decision gates for operational routing."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from curvature_console.infrastructure.operational_request import OperationalRequest


class DecisionGateDomain(StrEnum):
    PRODUCT_DIRECTION = "PRODUCT_DIRECTION"
    IMPLEMENTATION_PLAN_APPROVAL = "IMPLEMENTATION_PLAN_APPROVAL"
    CANON_OR_ART = "CANON_OR_ART"
    COST_OR_PURCHASE = "COST_OR_PURCHASE"
    INSTALLATION = "INSTALLATION"
    SECURITY = "SECURITY"
    REPOSITORY_MUTATION = "REPOSITORY_MUTATION"
    CROSS_DEPARTMENT_CONFLICT = "CROSS_DEPARTMENT_CONFLICT"


@dataclass(frozen=True, slots=True)
class OperationalDecisionGate:
    """A concrete operator stop inferred from authority and consequence."""

    domain: DecisionGateDomain
    reason: str
    question: str
    options: tuple[str, ...]
    consequences: tuple[str, ...]
    action_types: tuple[str, ...]


_MARKERS: tuple[tuple[DecisionGateDomain, tuple[str, ...]], ...] = (
    (
        DecisionGateDomain.CROSS_DEPARTMENT_CONFLICT,
        (
            "unresolved conflict",
            "departments disagree",
            "cross-department arbitration",
            "cannot reconcile",
            "conflicting recommendations",
        ),
    ),
    (
        DecisionGateDomain.CANON_OR_ART,
        (
            "canon decision",
            "change canon",
            "art direction",
            "visual direction",
            "visual identity",
            "ascii+ identity",
            "abandon the ascii+",
            "narrative canon",
            "lore decision",
        ),
    ),
    (
        DecisionGateDomain.PRODUCT_DIRECTION,
        (
            "product direction",
            "project direction",
            "scope decision",
            "change scope",
            "milestone approval",
            "priority decision",
            "roadmap decision",
        ),
    ),
    (
        DecisionGateDomain.COST_OR_PURCHASE,
        (
            "paid service",
            "purchase",
            "budget approval",
            "incur cost",
            "subscription",
            "licence fee",
            "license fee",
        ),
    ),
    (
        DecisionGateDomain.INSTALLATION,
        (
            "install dependency",
            "install package",
            "system installation",
            "apt install",
            "pip install",
            "conda install",
        ),
    ),
    (
        DecisionGateDomain.SECURITY,
        (
            "security-sensitive",
            "credential",
            "secret key",
            "api key",
            "access token",
            "elevated permission",
            "sudo",
            "firewall",
        ),
    ),
    (
        DecisionGateDomain.REPOSITORY_MUTATION,
        (
            "commit and push",
            "push to origin",
            "merge to main",
            "delete branch",
            "rewrite history",
            "force push",
            "repository write",
            "repository mutation",
        ),
    ),
)


def evaluate_operational_request_gate(
    request: OperationalRequest,
) -> OperationalDecisionGate | None:
    """Return an operator gate only for authority- or consequence-owned work."""

    text = "\n".join(
        (
            request.title,
            request.task,
            request.relevant_context,
            request.expected_output,
            *request.constraints,
            *request.acceptance_criteria,
        )
    ).casefold()
    if _is_implementation_plan_approval_request(request):
        return _gate_for_domain(
            DecisionGateDomain.IMPLEMENTATION_PLAN_APPROVAL,
            "implementation plan approval",
        )

    action_text = "\n".join((request.title, request.task)).casefold()
    for domain, markers in _MARKERS:
        # Product/canon gates must be requested by the action itself. Context,
        # constraints and acceptance criteria often describe the governing direction
        # that revision work must preserve; those references must not create a new
        # operator stop. Consequence gates (cost/install/security/repository/etc.)
        # still inspect the complete request because the risky consequence may be
        # stated outside the title/task.
        search_text = (
            action_text
            if domain in {DecisionGateDomain.PRODUCT_DIRECTION, DecisionGateDomain.CANON_OR_ART}
            else text
        )
        matched = next((marker for marker in markers if marker in search_text), None)
        if matched is not None:
            return _gate_for_domain(domain, matched)
    return None


def _is_implementation_plan_approval_request(request: OperationalRequest) -> bool:
    """Match approval intent without trapping revision work that merely mentions approval."""

    title = request.title.casefold().strip()
    task = request.task.casefold().strip()
    action_text = f"{title}\n{task}"
    plan_terms = ("implementation plan", "implementation-plan")
    if not any(term in action_text for term in plan_terms):
        return False

    # Approval gates are triggered by the requested action itself, not by context such as
    # "the revised plan will later require approval".  This keeps REVISE/AMEND work
    # routable to Core while still gating an explicit approval of a revised plan.
    approval_title_markers = (
        "approve ",
        "approval ",
        "authorize ",
        "authorization ",
        "approve:",
        "authorize:",
    )
    approval_task_prefixes = (
        "approve ",
        "authorize ",
        "request approval",
        "request authorization",
        "decide whether to approve",
        "decide whether to authorize",
        "return a plan-approval decision",
    )
    return any(marker in title for marker in approval_title_markers) or task.startswith(
        approval_task_prefixes
    )


def render_operator_decision_stop(gate: OperationalDecisionGate) -> str:
    """Render a structured decision request understood by attention classification."""

    options = "\n".join(f"- {item}" for item in gate.options)
    consequences = "\n".join(f"- {item}" for item in gate.consequences)
    return (
        "workflow_state: AWAITING_OPERATOR_DECISION\n"
        f"decision_domain: {gate.domain.value}\n"
        f"operator_decision: {gate.question}\n"
        f"operator_options:\n{options}\n"
        f"operator_consequences:\n{consequences}\n"
        f"decision_reason: {gate.reason}"
    )


def _gate_for_domain(
    domain: DecisionGateDomain,
    matched_marker: str,
) -> OperationalDecisionGate:
    reason = (
        f"Operational request matched the operator-owned {domain.value} "
        f"boundary via: {matched_marker}."
    )
    if domain is DecisionGateDomain.IMPLEMENTATION_PLAN_APPROVAL:
        return OperationalDecisionGate(
            domain,
            reason,
            "Should the proposed Chronicle implementation plan be approved?",
            (
                "Approve the proposed implementation plan.",
                "Reject the proposed implementation plan.",
                "Request a revised implementation plan.",
            ),
            (
                "Approval authorizes the plan to proceed within its stated scope.",
                "Rejection prevents the plan from proceeding.",
                "Revision returns the plan to the source department for amendment before implementation begins.",
            ),
            ("APPROVE", "REJECT", "REVISE"),
        )
    if domain is DecisionGateDomain.CROSS_DEPARTMENT_CONFLICT:
        return OperationalDecisionGate(
            domain,
            reason,
            "Which department recommendation should govern this unresolved conflict?",
            ("Choose the first department position.", "Choose the second department position.", "Return both departments for reconciliation."),
            ("A choice authorizes the selected direction.", "Reconciliation pauses execution but preserves both positions."),
            ("APPROVE", "APPROVE", "REVISE"),
        )
    if domain in {DecisionGateDomain.PRODUCT_DIRECTION, DecisionGateDomain.CANON_OR_ART}:
        return OperationalDecisionGate(
            domain,
            reason,
            "Should this operator-owned direction change be approved?",
            ("Approve the proposed change.", "Reject the proposed change.", "Ask for revised options."),
            ("Approval changes the governing project direction.", "Rejection preserves the current direction.", "Revision pauses execution pending a new proposal."),
            ("APPROVE", "REJECT", "REVISE"),
        )
    if domain is DecisionGateDomain.COST_OR_PURCHASE:
        return OperationalDecisionGate(
            domain,
            reason,
            "Should the proposed cost or purchase be authorized?",
            ("Approve the expenditure.", "Reject the expenditure.", "Request a free or lower-cost alternative."),
            ("Approval may create a financial commitment.", "Rejection prevents the purchase.", "An alternative request pauses the current route."),
            ("APPROVE", "REJECT", "REVISE"),
        )
    if domain is DecisionGateDomain.INSTALLATION:
        return OperationalDecisionGate(
            domain,
            reason,
            "Should the proposed installation or dependency change be authorized?",
            ("Approve installation.", "Reject installation.", "Request a no-install alternative."),
            ("Approval changes the local runtime or dependency set.", "Rejection preserves the current environment.", "An alternative may reduce capability or increase implementation effort."),
            ("APPROVE", "REJECT", "REVISE"),
        )
    if domain is DecisionGateDomain.SECURITY:
        return OperationalDecisionGate(
            domain,
            reason,
            "Should the proposed security-sensitive action be authorized?",
            ("Approve the action with the stated scope.", "Reject the action.", "Request a least-privilege alternative."),
            ("Approval may expose credentials or change access controls.", "Rejection preserves existing security boundaries.", "A least-privilege alternative may require redesign."),
            ("APPROVE", "REJECT", "REVISE"),
        )
    return OperationalDecisionGate(
        domain,
        reason,
        "Should the proposed repository mutation be authorized?",
        ("Approve the repository mutation.", "Reject the mutation.", "Run validation and prepare a patch only — no commit or push."),
        ("Approval changes shared repository state.", "Rejection leaves the repository unchanged.", "The preview runs validation and prepares review material without committing or pushing."),
        ("APPROVE", "REJECT", "REQUEST_NON_MUTATING_PREVIEW"),
    )
