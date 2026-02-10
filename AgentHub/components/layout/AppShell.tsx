"use client";

import type { ReactNode } from "react";
import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, Bot, Settings, ChevronLeft, ChevronRight, Menu, X } from "lucide-react";
import { APP_NAME } from "@/lib/config";

interface AppShellProps {
  children: ReactNode;
  title?: string;
  subtitle?: string;
}

function NavItem({
  href,
  label,
  icon,
  isActive,
  isCollapsed,
}: {
  href: string;
  label: string;
  icon: ReactNode;
  isActive: boolean;
  isCollapsed: boolean;
}) {
  return (
    <Link
      href={href}
      className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all text-sm ${
        isActive
          ? "bg-blue-500/20 text-blue-400"
          : "text-slate-400 hover:bg-slate-800/50 hover:text-white"
      } ${isCollapsed ? "justify-center" : ""}`}
      title={isCollapsed ? label : undefined}
    >
      <span className="w-5 h-5 flex-shrink-0">{icon}</span>
      {!isCollapsed && <span className="truncate">{label}</span>}
    </Link>
  );
}

export function AppShell({
  children,
  title = "Dashboard",
}: AppShellProps) {
  const pathname = usePathname();
  const [agentsOpen, setAgentsOpen] = useState(true);
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  return (
    <div className="h-screen bg-slate-100 overflow-hidden">
      <div className="flex h-screen">
        {/* Mobile Overlay */}
        {isMobileMenuOpen && (
          <div
            className="fixed inset-0 z-40 bg-slate-900/80 md:hidden"
            onClick={() => setIsMobileMenuOpen(false)}
          />
        )}

        {/* Desktop Sidebar */}
        <aside
          className={`hidden h-screen flex-col border-r border-slate-800/50 bg-[#0d1321] transition-all duration-300 md:flex flex-shrink-0 ${
            isCollapsed ? "w-16" : "w-64"
          }`}
        >
          <div className="flex h-16 items-center justify-between border-b border-slate-800/50 px-4">
            {!isCollapsed && (
              <>
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 bg-blue-500 rounded-lg flex items-center justify-center">
                    <Bot className="w-5 h-5 text-white" />
                  </div>
                  <span className="text-sm font-semibold tracking-tight text-white">
                    {APP_NAME}
                  </span>
                </div>
                <button
                  onClick={() => setIsCollapsed(!isCollapsed)}
                  className="p-1.5 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
                  aria-label="Collapse sidebar"
                >
                  <ChevronLeft className="w-5 h-5" />
                </button>
              </>
            )}
            {isCollapsed && (
              <button
                onClick={() => setIsCollapsed(!isCollapsed)}
                className="p-1.5 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
                aria-label="Expand sidebar"
              >
                <ChevronRight className="w-5 h-5" />
              </button>
            )}
          </div>

          <nav className="flex flex-1 flex-col overflow-y-auto py-4 px-2">
            <div className="flex-grow space-y-1">
              <NavItem
                href="/"
                label="Dashboard"
                icon={<LayoutDashboard className="w-5 h-5" />}
                isActive={pathname === "/"}
                isCollapsed={isCollapsed}
              />

              <div>
                <div className="relative">
                  <NavItem
                    href="/agents"
                    label="Agents"
                    icon={<Bot className="w-5 h-5" />}
                    isActive={pathname.startsWith("/agents")}
                    isCollapsed={isCollapsed}
                  />
                  {!isCollapsed && (
                    <button
                      type="button"
                      onClick={(e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        setAgentsOpen((open) => !open);
                      }}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-600 hover:text-slate-400 transition-transform"
                    >
                      <span
                        className={`transition-transform ${
                          agentsOpen ? "rotate-0" : "-rotate-90"
                        }`}
                      >
                        ▾
                      </span>
                    </button>
                  )}
                </div>
                {agentsOpen && !isCollapsed && (
                  <div className="mt-2 space-y-1 pl-1">
                    <div className="px-3 text-xs font-semibold uppercase tracking-wide text-slate-600">
                      My Agents
                    </div>
                    <div className="mt-2 space-y-1 pl-1">
                      <div className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm text-slate-300">
                        <span className="h-2 w-2 rounded-full bg-emerald-500" />
                        <span className="truncate">CRE Chatbot</span>
                      </div>
                      <div className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm text-slate-400">
                        <span className="h-2 w-2 rounded-full bg-slate-600" />
                        <span className="truncate">Data Analyst</span>
                      </div>
                      <div className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm text-slate-300">
                        <span className="h-2 w-2 rounded-full bg-emerald-500" />
                        <span className="truncate">Sales Assistant</span>
                      </div>
                      <div className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm text-slate-300">
                        <span className="h-2 w-2 rounded-full bg-emerald-500" />
                        <span className="truncate">Customer Support Bot</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>

            <div className="mt-auto p-2 border-t border-slate-800/50 space-y-1">
              <NavItem
                href="/settings"
                label="Settings"
                icon={<Settings className="w-5 h-5" />}
                isActive={pathname.startsWith("/settings")}
                isCollapsed={isCollapsed}
              />
              <div
                className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all text-sm text-slate-400 hover:bg-slate-800/50 hover:text-white ${
                  isCollapsed ? "justify-center" : ""
                }`}
              >
                <div className="flex h-5 w-5 items-center justify-center rounded-full bg-blue-500 text-[10px] font-semibold text-white flex-shrink-0">
                  GB
                </div>
                {!isCollapsed && (
                  <span className="truncate text-sm">Gemechu Bulti</span>
                )}
              </div>
            </div>
          </nav>
        </aside>

        {/* Mobile Sidebar */}
        <aside
          className={`fixed inset-y-0 left-0 z-50 flex h-screen w-64 flex-col border-r border-slate-800/50 bg-[#0d1321] transition-transform duration-300 md:hidden ${
            isMobileMenuOpen ? "translate-x-0" : "-translate-x-full"
          }`}
        >
          <div className="flex h-16 items-center justify-between border-b border-slate-800/50 px-4">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-blue-500 rounded-lg flex items-center justify-center">
                <Bot className="w-5 h-5 text-white" />
              </div>
              <span className="text-sm font-semibold tracking-tight text-white">
                {APP_NAME}
              </span>
            </div>
            <button
              onClick={() => setIsMobileMenuOpen(false)}
              className="p-1.5 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
              aria-label="Close menu"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          <nav className="flex flex-1 flex-col overflow-y-auto py-4 px-2">
            <div className="flex-grow space-y-6">
              <div>
                <NavItem
                  href="/"
                  label="Dashboard"
                  icon={<LayoutDashboard className="w-5 h-5" />}
                  isActive={pathname === "/"}
                  isCollapsed={false}
                />
              </div>

              <div>
                <NavItem
                  href="/agents"
                  label="Agents"
                  icon={<Bot className="w-5 h-5" />}
                  isActive={pathname.startsWith("/agents")}
                  isCollapsed={false}
                />
                <button
                  type="button"
                  onClick={() => setAgentsOpen((open) => !open)}
                  className="flex w-full items-center justify-between gap-3 px-3 py-2.5 rounded-lg transition-all text-sm text-slate-400 hover:bg-slate-800/50 hover:text-white"
                >
                  <div className="flex items-center gap-3">
                    <Bot className="w-5 h-5 flex-shrink-0" />
                    <span className="truncate">AGENTS</span>
                  </div>
                  <span
                    className={`text-slate-600 transition-transform ${
                      agentsOpen ? "rotate-0" : "-rotate-90"
                    }`}
                  >
                    ▾
                  </span>
                </button>
                {agentsOpen && (
                  <div className="mt-2 space-y-1 pl-1">
                    <div className="px-3 text-xs font-semibold uppercase tracking-wide text-slate-600">
                      My Agents
                    </div>
                    <div className="mt-2 space-y-1 pl-1">
                      <div className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm text-slate-300">
                        <span className="h-2 w-2 rounded-full bg-emerald-500" />
                        <span className="truncate">CRE Chatbot</span>
                      </div>
                      <div className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm text-slate-400">
                        <span className="h-2 w-2 rounded-full bg-slate-600" />
                        <span className="truncate">Data Analyst</span>
                      </div>
                      <div className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm text-slate-300">
                        <span className="h-2 w-2 rounded-full bg-emerald-500" />
                        <span className="truncate">Sales Assistant</span>
                      </div>
                      <div className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm text-slate-300">
                        <span className="h-2 w-2 rounded-full bg-emerald-500" />
                        <span className="truncate">Customer Support Bot</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>

            <div className="mt-auto p-2 border-t border-slate-800/50 space-y-1">
              <NavItem
                href="/settings"
                label="Settings"
                icon={<Settings className="w-5 h-5" />}
                isActive={pathname.startsWith("/settings")}
                isCollapsed={false}
              />
              <div className="flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all text-sm text-slate-400 hover:bg-slate-800/50 hover:text-white">
                <div className="flex h-5 w-5 items-center justify-center rounded-full bg-blue-500 text-[10px] font-semibold text-white flex-shrink-0">
                  GB
                </div>
                <span className="truncate text-sm">Gemechu Bulti</span>
              </div>
            </div>
          </nav>
        </aside>

        <main className="flex-1 flex flex-col overflow-hidden bg-white">
          <header className="flex-shrink-0 border-b border-slate-200 px-4 py-4 md:px-10">
            <div className="flex items-center gap-4">
              <button
                onClick={() => setIsMobileMenuOpen(true)}
                className="md:hidden p-2 rounded-lg hover:bg-slate-100 text-slate-600 hover:text-slate-900 transition-colors"
                aria-label="Open menu"
              >
                <Menu className="w-5 h-5" />
              </button>
              <h1 className="text-lg font-semibold tracking-tight text-slate-900">
                {title}
              </h1>
            </div>
          </header>

          <div className="flex-1 overflow-y-auto px-4 py-6 md:px-10 md:py-8">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}

