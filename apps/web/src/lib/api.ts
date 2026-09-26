import {
  InvestigationResponse,
  InvestigationEvidenceTrace,
  InvestigationEvent,
  LineageData,
} from "@/types/investigation";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  data: unknown;

  constructor(message: string, status: number, data?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.data = data;
  }
}

async function request<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  try {
    const res = await fetch(url, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...options?.headers,
      },
      cache: "no-store",
    });

    if (!res.ok) {
      let errorData: unknown;
      try {
        errorData = await res.json();
      } catch {
        errorData = await res.text();
      }
      const message =
        typeof errorData === "object" && errorData !== null && "detail" in errorData
          ? String((errorData as { detail: unknown }).detail)
          : `Request to ${endpoint} failed with status ${res.status}`;
      throw new ApiError(message, res.status, errorData);
    }

    return (await res.json()) as T;
  } catch (err: unknown) {
    if (err instanceof ApiError) {
      throw err;
    }
    const message = err instanceof Error ? err.message : "Network error";
    throw new ApiError(`Unable to connect to ExceptionLineage API (${message})`, 0, err);
  }
}

export async function checkApiHealth(): Promise<{ status: string; service: string; version: string }> {
  return request<{ status: string; service: string; version: string }>("/health");
}

export async function fetchInvestigations(): Promise<InvestigationResponse[]> {
  return request<InvestigationResponse[]>("/api/investigations");
}

export async function fetchInvestigation(id: string): Promise<InvestigationResponse> {
  return request<InvestigationResponse>(`/api/investigations/${encodeURIComponent(id)}`);
}

export async function fetchInvestigationEvents(
  id: string,
  includeAgentEvents = true
): Promise<InvestigationEvent[]> {
  return request<InvestigationEvent[]>(
    `/api/investigations/${encodeURIComponent(id)}/events?include_agent_events=${includeAgentEvents}`
  );
}

export async function fetchInvestigationTrace(id: string): Promise<InvestigationEvidenceTrace> {
  return request<InvestigationEvidenceTrace>(
    `/api/investigations/${encodeURIComponent(id)}/trace`
  );
}

export async function fetchInvestigationLineage(id: string): Promise<LineageData> {
  return request<LineageData>(
    `/api/investigations/${encodeURIComponent(id)}/lineage`
  );
}

export async function createInvestigation(
  invoiceId: string,
  exceptionId?: string | null
): Promise<InvestigationResponse> {
  return request<InvestigationResponse>("/api/investigations", {
    method: "POST",
    body: JSON.stringify({
      invoice_id: invoiceId.trim(),
      exception_id: exceptionId?.trim() || null,
    }),
  });
}
