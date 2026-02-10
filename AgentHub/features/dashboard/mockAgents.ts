import type { Agent } from "@/types/agent";

export const mockAgents: Agent[] = [
  {
    id: "1",
    name: "CRE Chatbot",
    description: "This agent will be a CRE expert on answering any portfolio related questions.",
    type: "custom",
    status: "active",
    conversations30d: 0,
    lastUsedAt: null,
  },
  {
    id: "2",
    name: "Customer Support Bot",
    description: "Handles customer inquiries and support tickets.",
    type: "support_agent",
    status: "active",
    conversations30d: 0,
    lastUsedAt: null,
  },
  {
    id: "3",
    name: "Sales Assistant",
    description: "Qualifies leads and schedules demos.",
    type: "sales_agent",
    status: "active",
    conversations30d: 0,
    lastUsedAt: null,
  },
  {
    id: "4",
    name: "Data Analyst",
    description: "Analyzes business metrics and generates reports.",
    type: "analyst_agent",
    status: "draft",
    conversations30d: 0,
    lastUsedAt: null,
  },
  {
    id: "5",
    name: "Customer Support Bot",
    description: "Handles customer inquiries and support tickets.",
    type: "support",
    status: "active",
    conversations30d: 244,
    lastUsedAt: "2026-02-01T00:00:00Z",
  },
  {
    id: "6",
    name: "Sales Assistant",
    description: "Qualifies leads and schedules demos.",
    type: "sales",
    status: "active",
    conversations30d: 145,
    lastUsedAt: "2026-02-01T00:00:00Z",
  },
  {
    id: "7",
    name: "Data Analyst",
    description: "Analyzes business metrics and generates reports.",
    type: "analyst",
    status: "draft",
    conversations30d: 0,
    lastUsedAt: null,
  },
];


