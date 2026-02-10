"use client";

import { useState, useEffect } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { Card } from "@/components/common/Card";
import { CardSkeleton } from "@/components/common/CardSkeleton";
import { AgentsSection } from "@/features/dashboard/AgentsSection";
import { Bot, MessageSquare, Link as LinkIcon, Clock } from "lucide-react";

export default function Home() {
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Simulate loading
    const timer = setTimeout(() => setIsLoading(false), 1000);
    return () => clearTimeout(timer);
  }, []);

  return (
    <AppShell title="Dashboard" subtitle="Monitor your agents and performance">
      <section className="space-y-8">
        <div className="flex items-center justify-between pb-5">
          <p className="text-sm text-slate-500">
            Monitor your agents and performance
          </p>
          <button className="inline-flex items-center gap-2 rounded-lg bg-blue-500 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-400">
            <span className="text-lg leading-none">+</span>
            <span>Add Agent</span>
          </button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {isLoading ? (
            <>
              <CardSkeleton />
              <CardSkeleton />
              <CardSkeleton />
              <CardSkeleton />
            </>
          ) : (
            <>
              <Card>
            <div className="relative">
              <div className="absolute top-0 right-0 flex h-10 w-10 items-center justify-center rounded-lg bg-blue-50">
                <Bot className="h-5 w-5 text-blue-600" />
              </div>
              <p className="text-sm font-medium text-slate-500">Total Agents</p>
              <p className="mt-2 text-2xl font-bold text-slate-900">7</p>
            </div>
          </Card>

          <Card>
            <div className="relative">
              <div className="absolute top-0 right-0 flex h-10 w-10 items-center justify-center rounded-lg bg-blue-50">
                <MessageSquare className="h-5 w-5 text-blue-600" />
              </div>
              <p className="text-sm font-medium text-slate-500">
                Conversations (30d)
              </p>
              <p className="mt-2 text-2xl font-bold text-slate-900">389</p>
              <p className="mt-1 text-xs font-medium text-emerald-600">
                ↑ 12% from last month
              </p>
            </div>
          </Card>

          <Card>
            <div className="relative">
              <div className="absolute top-0 right-0 flex h-10 w-10 items-center justify-center rounded-lg bg-blue-50">
                <LinkIcon className="h-5 w-5 text-blue-600" />
              </div>
              <p className="text-sm font-medium text-slate-500">
                Tokens Used (30d)
              </p>
              <p className="mt-2 text-2xl font-bold text-slate-900">119.3K</p>
              <p className="mt-1 text-xs font-medium text-emerald-600">
                ↑ 8% from last month
              </p>
            </div>
          </Card>

          <Card>
            <div className="relative">
              <div className="absolute top-0 right-0 flex h-10 w-10 items-center justify-center rounded-lg bg-blue-50">
                <Clock className="h-5 w-5 text-blue-600" />
              </div>
              <p className="text-sm font-medium text-slate-500">
                Avg Response Time
              </p>
              <p className="mt-2 text-2xl font-bold text-slate-900">332ms</p>
              <p className="mt-1 text-xs font-medium text-red-600">
              ↓ 5% from last month
            </p>
          </div>
        </Card>
            </>
          )}
        </div>

        <div className="space-y-3">
          <h2 className="text-base font-semibold text-slate-900">
            Your Agents
          </h2>
          <AgentsSection />
        </div>
      </section>
    </AppShell>
  );
}
