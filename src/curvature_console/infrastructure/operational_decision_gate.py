"""Authority- and consequence-based decision gates for operational routing."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from curvature_console.infrastructure.operational_request import OperationalRequest


class DecisionGateDomain(StrEnum):
    PRODUCT_DIRECTION = "PRODUCT_DIRECTION"
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
            "visual identity",
            "visual direction",
            "final visual direction",
            "abandon the ascii+ identity",
            "replace the ascii+ identity",
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
    for domain, markers in _MARKERS:
        matched = next((marker for marker in markers if marker in text), None)
        if matched is not None:
            return _gate_for_domain(domain, matched)
    return None


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
    if domain is DecisionGateDomain.CROSS_DEPARTMENT_CONFLICT:
        return OperationalDecisionGate(
            domain,
            reason,
            "Which department recommendation should govern this unresolved conflict?",
            ("Choose the first department position.", "Choose the second department position.", "Return both departments for reconciliation."),
            ("A choice authorizes the selected direction.", "Reconciliation pauses execution but preserves both positions."),
        )
    if domain in {DecisionGateDomain.PRODUCT_DIRECTION, DecisionGateDomain.CANON_OR_ART}:
        return OperationalDecisionGate(
            domain,
            reason,
            "Should this operator-owned direction change be approved?",
            ("Approve the proposed change.", "Reject the proposed change.", "Ask for revised options."),
            ("Approval changes the governing project direction.", "Rejection preserves the current direction.", "Revision pauses execution pending a new proposal."),
        )
    if domain is DecisionGateDomain.COST_OR_PURCHASE:
        return OperationalDecisionGate(
            domain,
            reason,
            "Should the proposed cost or purchase be authorized?",
            ("Approve the expenditure.", "Reject the expenditure.", "Request a free or lower-cost alternative."),
            ("Approval may create a financial commitment.", "Rejection prevents the purchase.", "An alternative request pauses the current route."),
        )
    if domain is DecisionGateDomain.INSTALLATION:
        return OperationalDecisionGate(
            domain,
            reason,
            "Should the proposed installation or dependency change be authorized?",
            ("Approve installation.", "Reject installation.", "Request a no-install alternative."),
            ("Approval changes the local runtime or dependency set.", "Rejection preserves the current environment.", "An alternative may reduce capability or increase implementation effort."),
        )
    if domain is DecisionGateDomain.SECURITY:
        return OperationalDecisionGate(
            domain,
            reason,
            "Should the proposed security-sensitive action be authorized?",
            ("Approve the action with the stated scope.", "Reject the action.", "Request a least-privilege alternative."),
            ("Approval may expose credentials or change access controls.", "Rejection preserves existing security boundaries.", "A least-privilege alternative may require redesign."),
        )
    return OperationalDecisionGate(
        domain,
        reason,
        "Should the proposed repository mutation be authorized?",
        ("Approve the repository mutation.", "Reject the mutation.", "Request a patch or dry-run only."),
        ("Approval changes shared repository state.", "Rejection leaves the repository unchanged.", "A dry-run provides review material without mutation."),
    )
