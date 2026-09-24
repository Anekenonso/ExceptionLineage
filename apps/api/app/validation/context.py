"""Investigation context model and normalization for the deterministic validation engine."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from app.models.common import ensure_timezone_aware


def parse_decimal(val: Any) -> Decimal | None:
    """Parse monetary or numeric values to an exact Decimal without float drift."""
    if val is None:
        return None
    if isinstance(val, Decimal):
        return val
    if isinstance(val, (int, float)):
        return Decimal(str(val))
    if isinstance(val, str):
        cleaned = val.replace("$", "").replace(",", "").strip()
        if not cleaned:
            return None
        return Decimal(cleaned)
    return None


def parse_datetime(val: Any) -> datetime | None:
    """Parse ISO datetime string or datetime object into a timezone-aware UTC datetime."""
    if val is None:
        return None
    if isinstance(val, datetime):
        if val.tzinfo is None:
            return val.replace(tzinfo=timezone.utc)
        return val.astimezone(timezone.utc)
    if isinstance(val, str):
        cleaned = val.strip()
        if not cleaned:
            return None
        if cleaned.endswith("Z"):
            cleaned = cleaned[:-1] + "+00:00"
        dt = datetime.fromisoformat(cleaned)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    return None


def extract_dollar_amounts(text: str | None) -> list[Decimal]:
    """Extract explicit dollar amounts formatted as $XX,XXX.XX or $XXXX.XX from text."""
    if not text:
        return []
    # Match patterns like $10,200.00 or $12000.00 or $10500
    pattern = r"\$\s*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]{2})?|[0-9]+(?:\.[0-9]{2})?)"
    matches = re.findall(pattern, text)
    amounts: list[Decimal] = []
    for m in matches:
        try:
            amounts.append(Decimal(m.replace(",", "")))
        except Exception:
            continue
    return amounts


class InvestigationContext:
    """Normalized investigation context representing the lineage for an invoice.

    Contains the invoice, billed customer, governing contract, direct exception,
    associated approval, amendments, statements of work (SOWs), and evidentiary records.
    """

    def __init__(
        self,
        invoice: dict[str, Any],
        customer: dict[str, Any] | None = None,
        contract: dict[str, Any] | None = None,
        exception: dict[str, Any] | None = None,
        approval: dict[str, Any] | None = None,
        amendments: list[dict[str, Any]] | None = None,
        sows: list[dict[str, Any]] | None = None,
        evidence: list[dict[str, Any]] | None = None,
    ) -> None:
        self.invoice = invoice
        self.customer = customer
        self.contract = contract
        self.exception = exception
        self.approval = approval
        self.amendments = amendments or []
        self.sows = sows or []
        self.evidence = evidence or []

    @classmethod
    def from_lineage(cls, lineage: dict[str, Any]) -> InvestigationContext:
        """Construct an InvestigationContext from the output of get_invoice_lineage."""
        invoice = lineage.get("invoice")
        if not invoice:
            raise ValueError("Lineage must contain an 'invoice' node")
        return cls(
            invoice=invoice,
            customer=lineage.get("customer"),
            contract=lineage.get("contract"),
            exception=lineage.get("exception"),
            approval=lineage.get("approval"),
            amendments=lineage.get("amendments") or [],
            sows=lineage.get("sows") or [],
            evidence=lineage.get("evidence") or [],
        )

    # -------------------------------------------------------------------------
    # Core Invoice Properties
    # -------------------------------------------------------------------------

    @property
    def invoice_id(self) -> str:
        return self.invoice["id"]

    @property
    def invoice_customer_id(self) -> str:
        return self.invoice["customer_id"]

    @property
    def invoice_contract_id(self) -> str | None:
        return self.invoice.get("contract_id")

    @property
    def invoice_exception_id(self) -> str | None:
        return self.invoice.get("exception_id")

    @property
    def invoice_product_id(self) -> str | None:
        return self.invoice.get("product_id")

    @property
    def invoice_amount(self) -> Decimal:
        raw = self.invoice.get("amount")
        res = parse_decimal(raw)
        if res is None:
            raise ValueError(f"Invoice '{self.invoice_id}' has invalid amount: {raw}")
        return res

    @property
    def invoice_currency(self) -> str:
        return self.invoice.get("currency", "USD")

    @property
    def invoice_issued_at(self) -> datetime:
        raw = self.invoice.get("issued_at")
        res = parse_datetime(raw)
        if res is None:
            raise ValueError(f"Invoice '{self.invoice_id}' has invalid issued_at: {raw}")
        return res

    # -------------------------------------------------------------------------
    # Contract Properties
    # -------------------------------------------------------------------------

    @property
    def has_contract(self) -> bool:
        return self.contract is not None and bool(self.contract.get("id"))

    @property
    def contract_id(self) -> str | None:
        return self.contract.get("id") if self.contract else None

    @property
    def contract_customer_id(self) -> str | None:
        return self.contract.get("customer_id") if self.contract else None

    @property
    def contract_status(self) -> str | None:
        return self.contract.get("status") if self.contract else None

    @property
    def contract_effective_from(self) -> datetime | None:
        if not self.contract:
            return None
        return parse_datetime(self.contract.get("effective_from"))

    @property
    def contract_effective_until(self) -> datetime | None:
        if not self.contract:
            return None
        return parse_datetime(self.contract.get("effective_until"))

    @property
    def contract_baseline_rate(self) -> Decimal | None:
        """Derive standard contract baseline rate from contract clauses or exception."""
        # Check exception expected_amount first if present
        if self.exception and self.exception.get("expected_amount"):
            amt = parse_decimal(self.exception.get("expected_amount"))
            if amt is not None:
                return amt

        # Check evidence attached to contract
        if self.contract_id:
            for ev in self.evidence_for(self.contract_id):
                excerpt = ev.get("excerpt", "")
                amounts = extract_dollar_amounts(excerpt)
                if amounts:
                    return amounts[0]

        return None

    # -------------------------------------------------------------------------
    # Evidence & Entity Relationship Helpers
    # -------------------------------------------------------------------------

    def evidence_for(self, source_id: str) -> list[dict[str, Any]]:
        """Return all evidence records originating from a specific source entity."""
        return [ev for ev in self.evidence if ev.get("source_id") == source_id]

    def evidence_for_scope(self, scope: str) -> list[dict[str, Any]]:
        """Return all evidence records explicitly tagged with a given scope."""
        return [ev for ev in self.evidence if ev.get("scope") == scope]

    def get_amendment(self, amendment_id: str) -> dict[str, Any] | None:
        for a in self.amendments:
            if a.get("id") == amendment_id:
                return a
        return None

    def get_amendment_scope(self, amendment_id: str) -> str | None:
        """Determine product or operational scope for an amendment."""
        # 1. From linked evidence scope
        for ev in self.evidence_for(amendment_id):
            scope = ev.get("scope")
            if scope:
                return scope

        # 2. From amendment description/title if matching invoice product
        amd = self.get_amendment(amendment_id)
        if amd:
            desc = f"{amd.get('title', '')} {amd.get('description', '')}"
            if self.invoice_product_id and self.invoice_product_id in desc:
                return self.invoice_product_id

        return None

    def get_amendment_rate(self, amendment_id: str) -> Decimal | None:
        """Extract explicit dollar rate authorized under an amendment."""
        # Check evidence excerpt first
        for ev in self.evidence_for(amendment_id):
            amounts = extract_dollar_amounts(ev.get("excerpt"))
            if amounts:
                return amounts[0]

        # Check amendment description
        amd = self.get_amendment(amendment_id)
        if amd:
            amounts = extract_dollar_amounts(amd.get("description"))
            if amounts:
                return amounts[0]

        return None

    def get_sow(self, sow_id: str) -> dict[str, Any] | None:
        for s in self.sows:
            if s.get("id") == sow_id:
                return s
        return None

    def get_sow_scope(self, sow_id: str) -> str | None:
        """Determine product or operational scope for an SOW."""
        for ev in self.evidence_for(sow_id):
            if ev.get("scope"):
                return ev["scope"]
        sow = self.get_sow(sow_id)
        if sow and sow.get("scope"):
            return sow["scope"]
        return None

    def get_candidate_amendments(self) -> list[dict[str, Any]]:
        """Identify candidate amendments relevant to this invoice.

        Matches based on product scope, referenced rates, or contract association.
        """
        if not self.amendments:
            return []

        target_product = self.invoice_product_id
        target_amount = self.invoice_amount

        scope_matches: list[dict[str, Any]] = []
        rate_matches: list[dict[str, Any]] = []

        for amd in self.amendments:
            amd_id = amd["id"]
            amd_scope = self.get_amendment_scope(amd_id)
            amd_rate = self.get_amendment_rate(amd_id)

            if target_product and amd_scope == target_product:
                scope_matches.append(amd)
            elif amd_rate == target_amount:
                rate_matches.append(amd)

        if scope_matches:
            return scope_matches
        if rate_matches:
            return rate_matches

        return list(self.amendments)
