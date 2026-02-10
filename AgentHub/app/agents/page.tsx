"use client";

import { AppShell } from "@/components/layout/AppShell";
import { AgentsGrid } from "@/features/agents/components/AgentsGrid";

export default function AgentsPage() {
  return (
    <AppShell title="Agents">
      <div className="space-y-6">
        <p className="text-sm text-slate-500">
          Select an agent from the sidebar to test it, or create a new one.
        </p>
        <AgentsGrid />
      </div>
    </AppShell>
  );
}

