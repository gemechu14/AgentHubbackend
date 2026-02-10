import type { Agent } from "@/types/agent";
import { AgentCard } from "./AgentCard";

interface AgentsListProps {
  agents: Agent[];
}

export function AgentsList({ agents }: AgentsListProps) {
  if (agents.length === 0) {
    return (
      <p className="text-sm text-slate-400">
        No agents yet. Create your first agent to get started.
      </p>
    );
  }

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      {agents.map((agent) => (
        <AgentCard key={agent.id} agent={agent} />
      ))}
    </div>
  );
}


