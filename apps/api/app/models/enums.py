from enum import Enum


class ValidationStatus(str, Enum):
    """Result status of a deterministic validation check.

    Note: UNKNOWN is a legitimate state and must never be coerced to PASS or FAIL.
    """

    PASS = "PASS"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"


class InvestigationStatus(str, Enum):
    """Lifecycle status of an ExceptionLineage investigation."""

    # Active states
    QUEUED = "QUEUED"
    INVESTIGATING = "INVESTIGATING"
    VALIDATING = "VALIDATING"

    # Terminal / outcome states
    VERIFIED = "VERIFIED"
    NOT_VERIFIED = "NOT_VERIFIED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    FAILED = "FAILED"


class ApprovalStatus(str, Enum):
    """Status of an approval associated with an operational exception."""

    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class ContractStatus(str, Enum):
    """Status of a governing enterprise contract."""

    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    TERMINATED = "TERMINATED"


class InvestigationEventType(str, Enum):
    """Type of auditable event during an investigation."""

    INPUT = "INPUT"
    EVIDENCE_FOUND = "EVIDENCE_FOUND"
    AGENT_DECISION = "AGENT_DECISION"
    TOOL_CALL = "TOOL_CALL"
    VALIDATION = "VALIDATION"
    ACTION_RESULT = "ACTION_RESULT"
