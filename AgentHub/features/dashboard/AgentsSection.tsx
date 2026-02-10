"use client";

import { AgentsTable } from "./AgentsTable";
import { mockAgents } from "./mockAgents";

export function AgentsSection() {
  return <AgentsTable agents={mockAgents} />;
}

