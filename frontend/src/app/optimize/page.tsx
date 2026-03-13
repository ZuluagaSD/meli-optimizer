"use client";

import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { api, type ListingSummary, type TitleOptimization } from "@/lib/api";
import { cn, completenessColor } from "@/lib/utils";

export default function OptimizePage() {
  return (
    <Suspense
      fallback={
        <div className="p-8">
          <div className="mb-2 h-8 w-56 skeleton" />
          <div className="mb-6 h-4 w-80 skeleton" />
          <div className="h-96 skeleton" />
        </div>
      }
    >
      <OptimizeContent />
    </Suspense>
  );
}

function OptimizeContent() {
  const searchParams = useSearchParams();
  const preselectedListing = searchParams.get("listing");
  const [listings, setListings] = useState<ListingSummary[]>([]);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [bulkResults, setBulkResults] = useState<Map<string, TitleOptimization>>(new Map());
  const [processing, setProcessing] = useState(false);
  const [progress, setProgress] = useState({ done: 0, total: 0 });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getListings({ page_size: 100, sort_by: "attribute_completeness_pct", sort_order: "asc" })
      .then((data) => {
        setListings(data.items);
        if (preselectedListing) {
          setSelectedIds(new Set([preselectedListing]));
        }
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [preselectedListing]);

  function toggleSelection(id: string) {
    const next = new Set(selectedIds);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    setSelectedIds(next);
  }

  function selectAll() {
    if (selectedIds.size === listings.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(listings.map((l) => l.id)));
    }
  }

  async function handleBulkOptimize() {
    const ids = Array.from(selectedIds);
    setProcessing(true);
    setProgress({ done: 0, total: ids.length });
    const results = new Map<string, TitleOptimization>();

    for (const id of ids) {
      try {
        const result = await api.optimizeTitle(id);
        results.set(id, result);
      } catch {
        // skip failed
      }
      setProgress((prev) => ({ ...prev, done: prev.done + 1 }));
    }

    setBulkResults(results);
    setProcessing(false);
  }

  return (
    <div className="p-8">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Bulk Optimization</h1>
        <p className="mt-1 text-sm text-gray-500">
          Select listings to generate optimized titles in bulk.
        </p>
      </div>

      {/* Actions */}
      <div className="mb-5 flex items-center gap-3">
        <button
          onClick={selectAll}
          disabled={listings.length === 0}
          className="inline-flex items-center gap-1.5 rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-40"
        >
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
            {selectedIds.size === listings.length && listings.length > 0 ? (
              <path strokeLinecap="round" strokeLinejoin="round" d="m9.75 9.75 4.5 4.5m0-4.5-4.5 4.5M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
            ) : (
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
            )}
          </svg>
          {selectedIds.size === listings.length && listings.length > 0 ? "Deselect All" : "Select All"}
        </button>
        <button
          onClick={handleBulkOptimize}
          disabled={processing || selectedIds.size === 0}
          className="inline-flex items-center gap-2 rounded-lg bg-brand-500 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-600 disabled:opacity-40"
        >
          {processing ? (
            <>
              <span className="spinner border-white border-r-transparent" />
              Processing {progress.done}/{progress.total}...
            </>
          ) : (
            <>
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904 9 18.75l-.813-2.846a4.5 4.5 0 0 0-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 0 0 3.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 0 0 3.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 0 0-3.09 3.09Z" />
              </svg>
              Optimize {selectedIds.size} Listing{selectedIds.size !== 1 ? "s" : ""}
            </>
          )}
        </button>

        {processing && (
          <div className="flex-1">
            <div className="h-1.5 overflow-hidden rounded-full bg-gray-100">
              <div
                className="h-full rounded-full bg-brand-500"
                style={{ width: `${progress.total > 0 ? (progress.done / progress.total) * 100 : 0}%` }}
              />
            </div>
          </div>
        )}
      </div>

      {/* Table */}
      <div className="overflow-hidden rounded-xl border border-gray-200/60 bg-white shadow-sm">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-100 bg-gray-50/80">
              <th className="w-12 px-4 py-3"></th>
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500">Title</th>
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500">Market</th>
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500">Completeness</th>
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500">Result</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50">
            {loading ? (
              Array.from({ length: 5 }).map((_, i) => (
                <tr key={i}>
                  <td className="px-4 py-3.5"><div className="h-4 w-4 skeleton" /></td>
                  <td className="px-4 py-3.5"><div className="h-4 w-48 skeleton" /></td>
                  <td className="px-4 py-3.5"><div className="h-4 w-12 skeleton" /></td>
                  <td className="px-4 py-3.5"><div className="h-4 w-10 skeleton" /></td>
                  <td className="px-4 py-3.5"><div className="h-4 w-32 skeleton" /></td>
                </tr>
              ))
            ) : listings.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-4 py-16 text-center">
                  <div className="mx-auto mb-3 flex h-10 w-10 items-center justify-center rounded-full bg-gray-100">
                    <svg className="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904 9 18.75l-.813-2.846a4.5 4.5 0 0 0-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 0 0 3.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 0 0 3.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 0 0-3.09 3.09Z" />
                    </svg>
                  </div>
                  <p className="text-sm font-medium text-gray-900">No listings to optimize</p>
                  <p className="mt-1 text-sm text-gray-500">
                    Sync your MeLi listings first from the Dashboard.
                  </p>
                </td>
              </tr>
            ) : (
              listings.map((listing) => {
                const result = bulkResults.get(listing.id);
                return (
                  <tr key={listing.id} className={cn("hover:bg-gray-50/50", selectedIds.has(listing.id) && "bg-brand-50/30")}>
                    <td className="px-4 py-3.5">
                      <input
                        type="checkbox"
                        checked={selectedIds.has(listing.id)}
                        onChange={() => toggleSelection(listing.id)}
                        className="h-4 w-4 rounded border-gray-300 text-brand-500 focus:ring-brand-500/20"
                      />
                    </td>
                    <td className="max-w-xs truncate px-4 py-3.5 text-sm">
                      <Link
                        href={`/listings/${listing.id}`}
                        className="font-medium text-gray-900 hover:text-brand-600"
                      >
                        {listing.title}
                      </Link>
                    </td>
                    <td className="px-4 py-3.5 text-sm text-gray-500">{listing.site_id}</td>
                    <td className="px-4 py-3.5 text-sm">
                      <div className="flex items-center gap-2">
                        <div className="h-1.5 w-12 overflow-hidden rounded-full bg-gray-100">
                          <div
                            className={cn(
                              "h-full rounded-full",
                              listing.attribute_completeness_pct >= 80
                                ? "bg-green-500"
                                : listing.attribute_completeness_pct >= 50
                                  ? "bg-amber-400"
                                  : "bg-red-500"
                            )}
                            style={{ width: `${listing.attribute_completeness_pct}%` }}
                          />
                        </div>
                        <span className={cn("text-xs font-medium", completenessColor(listing.attribute_completeness_pct))}>
                          {listing.attribute_completeness_pct}%
                        </span>
                      </div>
                    </td>
                    <td className="px-4 py-3.5 text-sm">
                      {result ? (
                        <div className="space-y-1">
                          {result.variants.map((v, i) => (
                            <p key={i} className="text-xs text-green-700">
                              <span className="font-medium">{i + 1}.</span> {v.title}
                            </p>
                          ))}
                        </div>
                      ) : processing && selectedIds.has(listing.id) ? (
                        <span className="inline-flex items-center gap-1.5 text-xs text-gray-400">
                          <span className="spinner h-3 w-3" />
                          Pending...
                        </span>
                      ) : null}
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
