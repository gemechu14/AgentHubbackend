import type { Agent } from "@/types/agent";
import { Badge } from "@/components/common/Badge";
import { formatLastUsed } from "@/lib/format";

interface AgentsTableProps {
  agents: Agent[];
}

function getTypeLabel(type: Agent["type"]) {
  switch (type) {
    case "custom":
      return "Custom";
    case "analyst":
    case "analyst_agent":
      return "Analyst Agent";
    case "support":
    case "support_agent":
      return "Support Agent";
    case "sales":
    case "sales_agent":
      return "Sales Agent";
    default:
      return type;
  }
}

export function AgentsTable({ agents }: AgentsTableProps) {
  if (agents.length === 0) {
    return (
      <p className="text-sm text-slate-500">
        No agents yet. Create your first agent to get started.
      </p>
    );
  }

  return (
    <div className="overflow-hidden rounded-xl border border-slate-200 bg-white">
      <div className="overflow-x-auto">
        <table className="min-w-full border-separate border-spacing-0 text-sm">
          <thead>
            <tr className="bg-slate-50 text-left text-[11px] font-semibold uppercase tracking-wide text-slate-500">
              <th className="px-4 py-3">Agent Name</th>
              <th className="px-4 py-3">Type</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Last Used</th>
              <th className="px-4 py-3 text-right">Conversations (30d)</th>
            </tr>
          </thead>
          <tbody>
            {agents.map((agent) => {
              const isActive = agent.status === "active";
              return (
                <tr key={agent.id} className="border-t border-slate-200">
                  <td className="px-4 py-4 align-top">
                    <div className="flex items-start gap-3">
                      <div className="mt-0.5 flex h-9 w-9 items-center justify-center rounded-lg bg-blue-50 text-blue-600">
                        <span className="text-xs font-semibold">A</span>
                      </div>
                      <div className="min-w-0">
                        <p className="truncate font-semibold text-slate-900">
                          {agent.name}
                        </p>
                        <p className="line-clamp-1 text-xs text-slate-500">
                          {agent.description}
                        </p>
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-4 align-top">
                    <Badge variant="default">{getTypeLabel(agent.type)}</Badge>
                  </td>
                  <td className="px-4 py-4 align-top">
                    <Badge variant={isActive ? "success" : "warning"}>
                      {isActive ? "Active" : "Draft"}
                    </Badge>
                  </td>
                  <td className="px-4 py-4 align-top text-slate-600">
                    {formatLastUsed(agent.lastUsedAt)}
                  </td>
                  <td className="px-4 py-4 align-top text-right font-semibold text-slate-900">
                    {agent.conversations30d}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}


