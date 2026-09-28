import { InvestigationResponse } from "@/types/investigation";

/**
 * Single transient in-memory slot for the active "Test Your Own Case" review.
 *
 * CRITICAL ARCHITECTURAL INVARIANTS:
 * 1. Uploaded case results exist only in transient browser memory for the
 *    current review session and are NEVER written to localStorage, sessionStorage,
 *    IndexedDB, or cookies.
 * 2. Storing a new test investigation immediately replaces and releases the previous one.
 * 3. Clearing or navigating away releases the transient case from memory.
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
