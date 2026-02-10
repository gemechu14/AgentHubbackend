"use client";

import { mockAgents } from "@/features/dashboard/mockAgents";
import { AgentCard } from "./AgentCard";

export function AgentsGrid() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {mockAgents.map((agent) => (
        <AgentCard key={agent.id} agent={agent} />
      ))}
    </div>
  );
}

