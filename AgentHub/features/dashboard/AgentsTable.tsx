import type { Agent } from "@/types/agent";
import { Bot } from "lucide-react";

interface AgentsTableProps {
  agents: Agent[];
}

export function AgentsTable({ agents }: AgentsTableProps) {
  return (
    <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm">
      <table className="min-w-full divide-y divide-slate-200 text-sm">
        <thead className="bg-slate-50">
          <tr>
            <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">
              Agent Name
            </th>
            <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">
              Type
            </th>
            <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">
              Status
            </th>
            <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">
              Last Used
            </th>
            <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-slate-500">
              Conversations (30d)
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100 bg-white">
          {agents.map((agent) => (
            <tr key={agent.id} className="hover:bg-slate-50/60">
              <td className="px-6 py-4">
                <div className="flex items-center gap-3">
                  <div className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-lg bg-blue-50">
                    <Bot className="h-5 w-5 text-blue-600" />
                  </div>
                  <div className="flex flex-col min-w-0">
                    <span className="text-sm font-semibold text-slate-900 truncate">
                      {agent.name}
                    </span>
                    <span className="mt-1 text-xs text-slate-500 truncate">
                      {agent.description}
                    </span>
                  </div>
                </div>
              </td>
              <td className="px-4 py-4 text-xs text-slate-700 capitalize whitespace-nowrap">
                {agent.type.replace("_", " ")}
              </td>
              <td className="px-4 py-4 text-xs whitespace-nowrap">
                <span
                  className={`inline-flex items-center rounded-full px-2.5 py-0.5 font-medium ${
                    agent.status === "active"
                      ? "bg-emerald-50 text-emerald-700 ring-1 ring-emerald-100"
                      : "bg-slate-100 text-slate-700 ring-1 ring-slate-200"
                  }`}
                >
                  {agent.status === "active" ? "Active" : "Draft"}
                </span>
              </td>
              <td className="px-4 py-4 text-xs text-slate-600 whitespace-nowrap">
                {agent.lastUsedAt ? "Feb 1, 2026" : "Never"}
              </td>
              <td className="px-4 py-4 text-right text-sm font-semibold text-slate-900 whitespace-nowrap">
                {agent.conversations30d}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}


