import { InvestigationResponse } from "@/types/investigation";

/**
 * Ephemeral In-Memory Storage for "Test Your Own Case".
 *
 * CRITICAL ARCHITECTURAL INVARIANT:
 * Uploaded cases are NEVER persisted to localStorage, sessionStorage,
 * IndexedDB, cookies, or any remote/local cache.
 * They live strictly in request/session memory and are released when the
 * tab is closed or navigated away.
 */
const ephemeralInvestigations = new Map<string, InvestigationResponse>();

export function storeEphemeralInvestigation(inv: InvestigationResponse): void {
  if (inv.investigation_id) {
    ephemeralInvestigations.set(inv.investigation_id, inv);
  }
  if (inv.invoice_id) {
    ephemeralInvestigations.set(inv.invoice_id, inv);
  }
}

export function getEphemeralInvestigation(id: string): InvestigationResponse | undefined {
  return ephemeralInvestigations.get(id);
}

export function clearEphemeralInvestigations(): void {
  ephemeralInvestigations.clear();
}
