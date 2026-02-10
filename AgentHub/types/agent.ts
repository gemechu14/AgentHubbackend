export type AgentStatus = "active" | "draft";

export type AgentType =
  | "custom"
  | "analyst"
  | "support"
  | "sales"
  | "analyst_agent"
  | "support_agent"
  | "sales_agent";

export interface Agent {
  id: string;
  name: string;
  description: string;
  type: AgentType;
  status: AgentStatus;
  conversations30d: number;
  lastUsedAt: string | null;
}


