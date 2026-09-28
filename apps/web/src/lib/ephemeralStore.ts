import { InvestigationResponse } from "@/types/investigation";

/**
 * Single transient in-memory slot for the active "Test Your Own Case" review.
 *
 * CRITICAL ARCHITECTURAL INVARIANTS:
 * 1. The result is held only in transient browser memory and is replaced when another
 *    custom case is tested. It is never written to browser persistence such as
 *    localStorage, sessionStorage, IndexedDB, or cookies.
 * 2. Storing a new test investigation immediately replaces and releases the previous one.
 * 3. Explicit clearing releases the transient case from memory.
 */
let currentEphemeralInvestigation: InvestigationResponse | null = null;

export function storeEphemeralInvestigation(inv: InvestigationResponse): void {
  currentEphemeralInvestigation = inv;
}

export function getEphemeralInvestigation(id: string): InvestigationResponse | null {
  if (!currentEphemeralInvestigation) return null;
  if (
    currentEphemeralInvestigation.investigation_id === id ||
    currentEphemeralInvestigation.invoice_id === id
  ) {
    return currentEphemeralInvestigation;
  }
  return null;
}

export function clearEphemeralInvestigation(): void {
  currentEphemeralInvestigation = null;
}
