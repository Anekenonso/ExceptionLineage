"""Deterministic Validation Engine module for ExceptionLineage.

Evaluates explicit, auditable rules against retrieved graph investigation context
to determine transaction exception validity without LLMs, probabilistic reasoning,
or ground-truth shortcuts.
"""

from app.validation.context import InvestigationContext
from app.validation.engine import ValidationEngine
from app.validation.models import InvestigationOutcome, ValidationOutcome
from app.validation.rules import (
    AmendmentEffectivenessRule,
    AmendmentScopeRule,
    ApplicableAmendmentRule,
    ApprovalAuthorizationRule,
    AuthorizedAmountRule,
    BaseValidationRule,
    ConflictingAuthorityRule,
    ContractApplicabilityRule,
    CustomerGoverningContractRule,
    get_default_validation_rules,
)

__all__ = [
    "InvestigationContext",
    "ValidationEngine",
    "ValidationOutcome",
    "InvestigationOutcome",
    "BaseValidationRule",
    "CustomerGoverningContractRule",
    "ContractApplicabilityRule",
    "ConflictingAuthorityRule",
    "ApplicableAmendmentRule",
    "AmendmentEffectivenessRule",
    "AmendmentScopeRule",
    "ApprovalAuthorizationRule",
    "AuthorizedAmountRule",
    "get_default_validation_rules",
]
