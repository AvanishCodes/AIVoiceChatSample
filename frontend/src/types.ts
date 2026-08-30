export interface User {
  user_id: string;
  email: string;
  name: string;
  role: string;
  tenant_id: number | null;
  tenant_name: string | null;
  permissions: string[];
}

export interface DemoUser {
  email: string;
  name: string;
  role: string;
  tenant_id: number | null;
  tenant_name: string | null;
  description: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface SqlQueryResult {
  sql: string;
  explanation: string;
  results: Record<string, any>[];
  row_count: number;
  columns: string[];
  execution_time_ms: number;
  tenant_id?: number | null;
  warnings?: string[];
  error?: string | null;
}

export interface CustomerProfile {
  tenant_id: number;
  name: string;
  health_score: number;
  carr: number;
  modules_active: string[];
  contract_end_date: string;
  assigned_csm: string;
  fleet_size: number;
  onboarding_status: string;
  region: string;
  aliases?: string[];
}

export interface OperationalSnapshot {
  deliveries_last_30d: number;
  gallons_last_30d: number;
  fill_rate: number;
  emergency_orders_count: number;
  active_drivers_count: number;
  active_trucks_count: number;
  critical_tanks_count: number;
}

export interface EscalationDetails {
  level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  score: number;
  churn_risk: boolean;
  reasons: string[];
  action_plan: string[];
}

export interface TicketBrief {
  ticket_id?: number | null;
  tenant_id: number;
  tenant_name: string;
  customer_profile: CustomerProfile;
  escalation: EscalationDetails;
  inactive_module_warning?: string | null;
  duplicate_detection: {
    is_duplicate?: boolean;
    duplicate_of_ticket_id?: number | null;
    confidence?: number;
    duplicate_note?: string;
  };
  relevant_past_tickets: Array<{
    ticket_id: number;
    subject: string;
    status: string;
    priority: string;
    product_area: string;
    created_at: string;
    resolution?: string;
    similarity_score: number;
    is_explicit_ref?: boolean;
  }>;
  relevant_kb_articles: Array<{
    article_id: string;
    title: string;
    product_area: string;
    root_cause: string;
    resolution: string;
    relevance_score: number;
    updated_at: string;
  }>;
  recent_calls: Array<{
    call_id: string;
    date: string;
    topic: string;
    sentiment: string;
    competitor_mentioned: boolean;
    action_items: string[];
    summary: string;
  }>;
  operational_snapshot: OperationalSnapshot;
  suggested_response: string;
  summary_markdown: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  sqlResult?: SqlQueryResult | null;
  ticketBrief?: TicketBrief | null;
  audioBase64?: string | null;
}

export interface BenchmarkItem {
  id: number;
  question: string;
  category: string;
  expected_focus: string;
}

export interface SampleTicketScenario {
  scenario_id: string;
  title: string;
  scenario_type: string;
  description: string;
  ticket_data: {
    ticket_id?: number;
    tenant_id?: number;
    tenant_name?: string;
    subject: string;
    description: string;
    product_area?: string;
    priority?: string;
    submitter_email?: string;
  };
}
