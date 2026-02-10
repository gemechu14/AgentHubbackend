"use client";

import { useAgents } from "@/hooks/useAgents";
import { Card } from "@/components/common/Card";
import { AgentsTable } from "../components/AgentsTable";

export function AgentsOverview() {
  const { data, isLoading, error } = useAgents();

  if (isLoading) {
    return (
      <Card>
        <p className="text-sm text-slate-500">Loading agents…</p>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <p className="text-sm text-red-400">
          Failed to load agents: {error.message}
        </p>
      </Card>
    );
  }

  if (!data) {
    return null;
  }

  return <AgentsTable agents={data} />;
}

