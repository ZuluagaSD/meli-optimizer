"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api, type PaginatedListings } from "@/lib/api";
import { cn, formatCurrency, healthColor, completenessColor } from "@/lib/utils";

export default function ListingsPage() {
  const [data, setData] = useState<PaginatedListings | null>(null);
  const [siteFilter, setSiteFilter] = useState<string>("");
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [sortBy, setSortBy] = useState("attribute_completeness_pct");
  const [sortOrder, setSortOrder] = useState("asc");
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api
      .getListings({
        site_id: siteFilter || undefined,
        status: statusFilter || undefined,
        sort_by: sortBy,
        sort_order: sortOrder,
        page,
        page_size: 20,
      })
      .then(setData)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [siteFilter, statusFilter, sortBy, sortOrder, page]);

  const totalPages = data ? Math.ceil(data.total / data.page_size) : 0;

  return (
    <div className="p-8">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Listings</h1>
        <p className="mt-1 text-sm text-gray-500">Manage and optimize your Mercado Libre listings</p>
      </div>

      {/* Filters */}
      <div className="mb-5 flex flex-wrap items-center gap-3">
        <select
          value={siteFilter}
          onChange={(e) => { setSiteFilter(e.target.value); setPage(1); }}
          className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-700 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20"
        >
          <option value="">All Markets</option>
          <option value="MLA">Argentina (MLA)</option>
          <option value="MLB">Brasil (MLB)</option>
          <option value="MLM">Mexico (MLM)</option>
        </select>

        <select
          value={statusFilter}
          onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
          className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-700 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20"
        >
          <option value="">All Statuses</option>
          <option value="active">Active</option>
          <option value="paused">Paused</option>
          <option value="closed">Closed</option>
        </select>

        <select
          value={`${sortBy}:${sortOrder}`}
          onChange={(e) => {
            const [field, order] = e.target.value.split(":");
            setSortBy(field);
            setSortOrder(order);
            setPage(1);
          }}
          className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-700 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20"
        >
          <option value="attribute_completeness_pct:asc">Completeness (lowest first)</option>
          <option value="attribute_completeness_pct:desc">Completeness (highest first)</option>
          <option value="price:desc">Price (highest first)</option>
          <option value="price:asc">Price (lowest first)</option>
          <option value="last_synced_at:desc">Recently synced</option>
        </select>

        {data && (
          <span className="ml-auto text-sm text-gray-400">
            {data.total} listing{data.total !== 1 ? "s" : ""}
          </span>
        )}
      </div>

      {/* Table */}
      <div className="overflow-hidden rounded-xl border border-gray-200/60 bg-white shadow-sm">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-100 bg-gray-50/80">
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500">Title</th>
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500">Market</th>
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500">Status</th>
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500">Price</th>
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500">Health</th>
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500">Completeness</th>
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50">
            {loading ? (
              Array.from({ length: 5 }).map((_, i) => (
                <tr key={i}>
                  <td className="px-4 py-3.5"><div className="h-4 w-48 skeleton" /></td>
                  <td className="px-4 py-3.5"><div className="h-4 w-12 skeleton" /></td>
                  <td className="px-4 py-3.5"><div className="h-5 w-16 skeleton" /></td>
                  <td className="px-4 py-3.5"><div className="h-4 w-20 skeleton" /></td>
                  <td className="px-4 py-3.5"><div className="h-5 w-16 skeleton" /></td>
                  <td className="px-4 py-3.5"><div className="h-4 w-10 skeleton" /></td>
                  <td className="px-4 py-3.5"><div className="h-6 w-16 skeleton" /></td>
                </tr>
              ))
            ) : data?.items.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-4 py-16 text-center">
                  <div className="mx-auto mb-3 flex h-10 w-10 items-center justify-center rounded-full bg-gray-100">
                    <svg className="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M20.25 7.5l-.625 10.632a2.25 2.25 0 0 1-2.247 2.118H6.622a2.25 2.25 0 0 1-2.247-2.118L3.75 7.5m6 4.125 2.25 2.25m0 0 2.25 2.25M12 13.875l2.25-2.25M12 13.875l-2.25 2.25M3.375 7.5h17.25c.621 0 1.125-.504 1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125H3.375c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125Z" />
                    </svg>
                  </div>
                  <p className="text-sm font-medium text-gray-900">No listings found</p>
                  <p className="mt-1 text-sm text-gray-500">
                    Connect a MeLi account and sync to see your listings here.
                  </p>
                </td>
              </tr>
            ) : (
              data?.items.map((listing) => (
                <tr key={listing.id} className="hover:bg-gray-50/50">
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
                    <span
                      className={cn(
                        "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium capitalize",
                        listing.status === "active"
                          ? "bg-green-50 text-green-700"
                          : listing.status === "paused"
                            ? "bg-amber-50 text-amber-700"
                            : "bg-gray-100 text-gray-600"
                      )}
                    >
                      {listing.status}
                    </span>
                  </td>
                  <td className="px-4 py-3.5 text-sm font-medium text-gray-700">
                    {formatCurrency(listing.price, listing.currency_id)}
                  </td>
                  <td className="px-4 py-3.5 text-sm">
                    <span
                      className={cn(
                        "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium capitalize",
                        healthColor(listing.health_status)
                      )}
                    >
                      {listing.health_status || "unknown"}
                    </span>
                  </td>
                  <td className="px-4 py-3.5 text-sm">
                    <div className="flex items-center gap-2">
                      <div className="h-1.5 w-16 overflow-hidden rounded-full bg-gray-100">
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
                    <Link
                      href={`/optimize?listing=${listing.id}`}
                      className="inline-flex items-center gap-1 rounded-lg bg-brand-500 px-3 py-1.5 text-xs font-medium text-white hover:bg-brand-600"
                    >
                      <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904 9 18.75l-.813-2.846a4.5 4.5 0 0 0-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 0 0 3.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 0 0 3.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 0 0-3.09 3.09Z" />
                      </svg>
                      Optimize
                    </Link>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="mt-5 flex items-center justify-between">
          <p className="text-sm text-gray-500">
            Page {page} of {totalPages}
          </p>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage(Math.max(1, page - 1))}
              disabled={page === 1}
              className="inline-flex items-center gap-1 rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-40"
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 19.5 8.25 12l7.5-7.5" />
              </svg>
              Previous
            </button>
            <button
              onClick={() => setPage(Math.min(totalPages, page + 1))}
              disabled={page === totalPages}
              className="inline-flex items-center gap-1 rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-40"
            >
              Next
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="m8.25 4.5 7.5 7.5-7.5 7.5" />
              </svg>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
