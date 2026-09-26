export type InvestigationStatus =
  | "QUEUED"
  | "INVESTIGATING"
  | "VALIDATING"
  | "VERIFIED"
  | "NOT_VERIFIED"
  | "INSUFFICIENT_EVIDENCE"
  | "NEEDS_REVIEW"
  | "FAILED";

export type ValidationStatus = "PASS" | "FAIL" | "UNKNOWN";

export type InvestigationEventType =
  | "INPUT"
  | "EVIDENCE_FOUND"
  | "AGENT_DECISION"
  | "TOOL_CALL"
  | "VALIDATION"
  | "ACTION_RESULT"
  | "STATE_TRANSITION";

export interface ValidationResult {
  check_name: string;
  status: ValidationStatus;
  message?: string | null;
  evidence_ids?: string[];
  timestamp: string;
  is_required: boolean;
}

export interface AgentMetrics {
  total_agent_steps: number;
  tool_calls: number;
  successful_tool_calls: number;
  failed_tool_calls: number;
  investigation_duration_ms: number;
  evidence_items_collected: number;
  duplicate_tool_calls: number;
  termination_reason?: string | null;
  llm_calls?: number;
  llm_failures?: number;
  llm_retries?: number;
  malformed_actions?: number;
  prompt_tokens?: number | null;
  completion_tokens?: number | null;
  total_tokens?: number | null;
}

export interface InvestigationEvent {
  id: string;
  investigation_id: string;
  from_state?: InvestigationStatus | null;
  to_state?: InvestigationStatus | null;
  reason?: string | null;
  event_type: InvestigationEventType | string;
  message: string;
  timestamp: string;
  metadata?: Record<string, unknown>;
}

export interface TraceEvent {
  type: "input" | "agent_decision" | "tool_call" | "graph_retrieval" | "validation" | "outcome" | string;
  timestamp?: string | null;
  step?: number | null;
  action?: string | null;
  reason?: string | null;
  arguments?: Record<string, unknown> | null;
  source?: string | null;
  relationships?: string[];
  evidence_ids?: string[];
  check?: string | null;
  status?: string | null;
  message?: string | null;
}

export interface InvestigationEvidenceTrace {
  investigation_id: string;
  input: {
    invoice_id: string;
    exception_id?: string | null;
    created_at?: string | null;
    data_notice?: string;
    [key: string]: unknown;
  };
  final_outcome: string;
  chain_verified: boolean;
  events: TraceEvent[];
  summary: {
    total_events?: number;
    agent_decisions_count?: number;
    tool_calls_count?: number;
    graph_retrievals_count?: number;
    validation_checks_count?: number;
    cited_evidence_count?: number;
    secrets_redacted?: boolean;
    is_simulated_dataset?: boolean;
    authority_boundary_preserved?: boolean;
    [key: string]: unknown;
  };
}

export interface EvidenceItem {
  id: string;
  evidence_type: string;
  source: string;
  source_id: string;
  title?: string | null;
  locator?: string | null;
  excerpt?: string | null;
  captured_at?: string;
  effective_from?: string | null;
  effective_until?: string | null;
  scope?: string | null;
  confidence?: number | null;
  amount?: string | number | null;
}

export interface CustomerData {
  id: string;
  name: string;
  external_id?: string | null;
  created_at?: string;
}

export interface ContractData {
  id: string;
  customer_id: string;
  title: string;
  effective_from: string;
  effective_until?: string | null;
  status: string;
  currency: string;
  created_at?: string;
  updated_at?: string | null;
}

export interface AmendmentData {
  id: string;
  contract_id: string;
  amendment_number: number;
  title: string;
  description?: string;
  effective_from: string;
  effective_until?: string | null;
  created_at?: string;
  updated_at?: string | null;
}

export interface SOWData {
  id: string;
  contract_id: string;
  reference: string;
  title: string;
  scope?: string;
  effective_from: string;
  effective_until?: string | null;
  created_at?: string;
  updated_at?: string | null;
}

export interface ExceptionData {
  id: string;
  contract_id: string;
  invoice_id?: string | null;
  exception_type: string;
  description: string;
  expected_amount?: string | number | null;
  actual_amount?: string | number | null;
  currency?: string;
  created_at?: string;
}

export interface ApprovalData {
  id: string;
  exception_id: string;
  approver: string;
  status: string;
  approved_at?: string | null;
  context_json?: string | null;
  created_at?: string;
}

export interface InvoiceData {
  id: string;
  customer_id: string;
  contract_id?: string | null;
  exception_id?: string | null;
  product_id?: string | null;
  amount: string | number;
  currency?: string;
  issued_at: string;
  due_at?: string | null;
  created_at?: string;
}

export interface LineageData {
  invoice?: InvoiceData | null;
  customer?: CustomerData | null;
  contract?: ContractData | null;
  exception?: ExceptionData | null;
  approval?: ApprovalData | null;
  amendments?: AmendmentData[];
  sows?: SOWData[];
  evidence?: EvidenceItem[];
}

export interface InvestigationResponse {
  investigation_id: string;
  invoice_id: string;
  exception_id?: string | null;
  status: InvestigationStatus;
  summary?: string | null;
  failure_reason?: string | null;
  created_at: string;
  updated_at?: string | null;
  validation_results?: ValidationResult[] | null;
  cited_evidence_ids: string[];
  agent_metrics?: AgentMetrics | null;
  events?: InvestigationEvent[] | null;
  agent_events?: InvestigationEvent[] | null;
  customer_id?: string | null;
  customer_name?: string | null;
  amount?: string | null;
  currency?: string | null;
  duration_seconds?: number | null;
  lineage?: LineageData | null;
}
