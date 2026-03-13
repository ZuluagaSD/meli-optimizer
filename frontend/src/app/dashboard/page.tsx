"use client";

import { useEffect, useState } from "react";
import { api, type DashboardStats, type MeliAccount } from "@/lib/api";
import { siteLabel } from "@/lib/utils";

function StatCard({
  label,
  value,
  sub,
  accent,
}: {
  label: string;
  value: string | number;
  sub?: string;
  accent?: "green" | "yellow" | "red" | "blue";
}) {
  const accentColors = {
    green: "bg-green-50 text-green-600",
    yellow: "bg-brand-50 text-brand-600",
    red: "bg-red-50 text-red-600",
    blue: "bg-blue-50 text-blue-600",
  };
  const dotColor = accent ? accentColors[accent] : "bg-gray-50 text-gray-500";

  return (
    <div className="rounded-xl border border-gray-100 bg-white p-5 shadow-sm">
      <div className="flex items-center gap-2">
        <span className={`inline-flex h-2 w-2 rounded-full ${dotColor.split(" ")[0]?.replace("bg-", "bg-")}`}>
          <span className={`h-2 w-2 rounded-full ${accent === "green" ? "bg-green-500" : accent === "yellow" ? "bg-brand-500" : accent === "red" ? "bg-red-500" : accent === "blue" ? "bg-blue-500" : "bg-gray-400"}`} />
        </span>
        <p className="text-sm font-medium text-gray-500">{label}</p>
      </div>
      <p className="mt-2 text-2xl font-bold text-gray-900">{value}</p>
      {sub && <p className="mt-1 text-xs text-gray-400">{sub}</p>}
    </div>
  );
}

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [accounts, setAccounts] = useState<MeliAccount[]>([]);
  const [syncing, setSyncing] = useState<string | null>(null);
  const [syncMsg, setSyncMsg] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.getDashboardStats().then(setStats).catch(() => {}),
      api.getMeliAccounts().then(setAccounts).catch(() => {}),
    ]).finally(() => setLoading(false));
  }, []);

  async function handleSync(accountId: string) {
    setSyncing(accountId);
    setSyncMsg("");
    try {
      const result = await api.syncListings(accountId);
      setSyncMsg(result.message);
      const newStats = await api.getDashboardStats();
      setStats(newStats);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Sync failed");
    } finally {
      setSyncing(null);
    }
  }

  if (loading) {
    return (
      <div className="p-8">
        <div className="mb-8 h-8 w-48 skeleton" />
        <div className="mb-6 h-5 w-40 skeleton" />
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-24 skeleton" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="mt-1 text-sm text-gray-500">Monitor your Mercado Libre listings performance</p>
      </div>

      {/* Connected Accounts */}
      <section className="mb-8">
        <h2 className="mb-4 text-sm font-semibold uppercase tracking-wider text-gray-400">
          Connected Accounts
        </h2>
        <div className="flex flex-wrap gap-4">
          {accounts.map((acc) => (
            <div
              key={acc.id}
              className="flex items-center gap-3 rounded-xl border border-gray-100 bg-white p-4 shadow-sm"
            >
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-brand-100 text-xs font-bold text-brand-700">
                {acc.site_id}
              </div>
              <div>
                <p className="text-sm font-medium text-gray-900">
                  {acc.nickname || `User ${acc.meli_user_id}`}
                </p>
                <p className="text-xs text-gray-500">{siteLabel(acc.site_id)}</p>
              </div>
              <button
                onClick={() => handleSync(acc.id)}
                disabled={syncing === acc.id}
                className="ml-4 flex items-center gap-1.5 rounded-lg bg-brand-500 px-3 py-1.5 text-xs font-medium text-white hover:bg-brand-600 disabled:opacity-50"
              >
                {syncing === acc.id ? (
                  <>
                    <span className="spinner h-3 w-3 border-white border-r-transparent" />
                    Syncing...
                  </>
                ) : (
                  <>
                    <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0 3.181 3.183a8.25 8.25 0 0 0 13.803-3.7M4.031 9.865a8.25 8.25 0 0 1 13.803-3.7l3.181 3.182" />
                    </svg>
                    Sync
                  </>
                )}
              </button>
            </div>
          ))}

          {/* Connect new */}
          <div className="flex items-center gap-3 rounded-xl border-2 border-dashed border-gray-200 bg-gray-50/50 p-4">
            <svg className="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
            </svg>
            <span className="text-sm font-medium text-gray-500">Connect:</span>
            {["MLA", "MLB", "MLM"].map((site) => (
              <a
                key={site}
                href={api.getMeliAuthUrl(site)}
                className="rounded-lg border border-gray-200 bg-white px-3 py-1.5 text-xs font-medium text-gray-600 shadow-sm hover:border-brand-300 hover:text-brand-600"
              >
                {site}
              </a>
            ))}
          </div>
        </div>

        {syncMsg && (
          <div className="mt-3 flex items-center gap-2 text-sm text-green-600">
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
            </svg>
            {syncMsg}
          </div>
        )}
        {error && (
          <div className="mt-3 flex items-center gap-2 text-sm text-red-600">
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9 3.75h.008v.008H12v-.008Z" />
            </svg>
            {error}
          </div>
        )}
      </section>

      {/* Stats Grid */}
      {stats ? (
        <section>
          <h2 className="mb-4 text-sm font-semibold uppercase tracking-wider text-gray-400">
            Overview
          </h2>
          <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
            <StatCard label="Total Listings" value={stats.total_listings} accent="blue" />
            <StatCard label="Active" value={stats.active_listings} accent="green" />
            <StatCard label="Avg Completeness" value={`${stats.avg_completeness}%`} accent="yellow" />
            <StatCard
              label="Need Attention"
              value={stats.listings_needing_attention}
              accent="red"
              sub="Below 70% completeness"
            />
            <StatCard label="Total Optimizations" value={stats.total_optimizations} accent="blue" />
            <StatCard label="Applied" value={stats.applied_optimizations} accent="green" />
            <StatCard label="Paused Listings" value={stats.paused_listings} accent="yellow" />
            <StatCard
              label="Markets"
              value={Object.keys(stats.site_distribution).length}
              sub={Object.entries(stats.site_distribution)
                .map(([k, v]) => `${k}: ${v}`)
                .join(", ")}
            />
          </div>

          {/* Health Distribution */}
          <div className="mt-6 rounded-xl border border-gray-100 bg-white p-6 shadow-sm">
            <h3 className="mb-4 text-sm font-semibold text-gray-900">Health Distribution</h3>
            <div className="flex flex-wrap gap-6">
              {Object.entries(stats.health_distribution).map(([status, count]) => (
                <div key={status} className="flex items-center gap-2.5">
                  <span
                    className={`inline-block h-3 w-3 rounded-full ${
                      status === "healthy"
                        ? "bg-green-500"
                        : status === "warning"
                          ? "bg-amber-400"
                          : status === "critical"
                            ? "bg-red-500"
                            : "bg-gray-300"
                    }`}
                  />
                  <span className="text-sm text-gray-600">
                    <span className="font-medium capitalize">{status}</span>
                    <span className="ml-1 text-gray-400">{count}</span>
                  </span>
                </div>
              ))}
            </div>
          </div>
        </section>
      ) : (
        /* Empty state when no stats */
        <section className="mt-4 rounded-2xl border-2 border-dashed border-gray-200 bg-gray-50/50 p-12 text-center">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-brand-100">
            <svg className="h-6 w-6 text-brand-600" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 0 1 3 19.875v-6.75ZM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V8.625ZM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V4.125Z" />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-gray-900">No data yet</h3>
          <p className="mx-auto mt-2 max-w-sm text-sm text-gray-500">
            Connect a Mercado Libre account above and sync your listings to see performance stats here.
          </p>
        </section>
      )}
    </div>
  );
}
