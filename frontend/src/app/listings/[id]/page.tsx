"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  api,
  type ListingDetail,
  type Competitor,
  type TitleOptimization,
  type AttributeOptimization,
} from "@/lib/api";
import { cn, formatCurrency, healthColor, completenessColor } from "@/lib/utils";

export default function ListingDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [listing, setListing] = useState<ListingDetail | null>(null);
  const [competitors, setCompetitors] = useState<Competitor[]>([]);
  const [titleOpt, setTitleOpt] = useState<TitleOptimization | null>(null);
  const [attrOpt, setAttrOpt] = useState<AttributeOptimization | null>(null);
  const [optimizing, setOptimizing] = useState(false);
  const [applying, setApplying] = useState<number | null>(null);
  const [message, setMessage] = useState("");

  useEffect(() => {
    if (!id) return;
    api.getListing(id).then(setListing).catch(() => router.push("/listings"));
    api.getCompetitors(id).then(setCompetitors).catch(() => {});
  }, [id, router]);

  async function handleOptimizeTitle() {
    if (!id) return;
    setOptimizing(true);
    setTitleOpt(null);
    setMessage("");
    try {
      const result = await api.optimizeTitle(id);
      setTitleOpt(result);
    } catch (err: unknown) {
      setMessage(err instanceof Error ? err.message : "Optimization failed");
    } finally {
      setOptimizing(false);
    }
  }

  async function handleOptimizeAttributes() {
    if (!id) return;
    setOptimizing(true);
    setAttrOpt(null);
    setMessage("");
    try {
      const result = await api.optimizeAttributes(id);
      setAttrOpt(result);
    } catch (err: unknown) {
      setMessage(err instanceof Error ? err.message : "Optimization failed");
    } finally {
      setOptimizing(false);
    }
  }

  async function handleApplyTitle(index: number) {
    if (!titleOpt) return;
    setApplying(index);
    try {
      await api.applyOptimization(titleOpt.optimization_id, index);
      setMessage("Title applied to MeLi!");
      if (id) {
        const updated = await api.getListing(id);
        setListing(updated);
      }
    } catch (err: unknown) {
      setMessage(err instanceof Error ? err.message : "Apply failed");
    } finally {
      setApplying(null);
    }
  }

  if (!listing) {
    return (
      <div className="p-8">
        <div className="mb-6 h-4 w-32 skeleton" />
        <div className="mb-2 h-8 w-96 skeleton" />
        <div className="mb-8 h-4 w-64 skeleton" />
        <div className="grid gap-6 lg:grid-cols-3">
          <div className="space-y-6 lg:col-span-2">
            <div className="h-40 skeleton" />
            <div className="h-60 skeleton" />
          </div>
          <div className="h-80 skeleton" />
        </div>
      </div>
    );
  }

  return (
    <div className="p-8">
      {/* Header */}
      <div className="mb-6">
        <button
          onClick={() => router.back()}
          className="mb-3 inline-flex items-center gap-1 text-sm text-gray-400 hover:text-gray-600"
        >
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 19.5 8.25 12l7.5-7.5" />
          </svg>
          Back to listings
        </button>
        <h1 className="text-2xl font-bold text-gray-900">{listing.title}</h1>
        <div className="mt-2 flex items-center gap-3">
          <span className="text-sm text-gray-400">{listing.meli_item_id}</span>
          <span className={cn("inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium", healthColor(listing.health_status))}>
            {listing.health_status || "unknown"}
          </span>
          <div className="flex items-center gap-1.5">
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
            <span className={cn("text-sm font-medium", completenessColor(listing.attribute_completeness_pct))}>
              {listing.attribute_completeness_pct}%
            </span>
          </div>
        </div>
      </div>

      {message && (
        <div className="mb-4 flex items-center gap-2 rounded-lg bg-blue-50 p-3 text-sm text-blue-700">
          <svg className="h-4 w-4 shrink-0" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="m11.25 11.25.041-.02a.75.75 0 0 1 1.063.852l-.708 2.836a.75.75 0 0 0 1.063.853l.041-.021M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9-3.75h.008v.008H12V8.25Z" />
          </svg>
          {message}
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Left column */}
        <div className="space-y-6 lg:col-span-2">
          {/* Images */}
          {listing.pictures && listing.pictures.length > 0 && (
            <div className="flex gap-2 overflow-x-auto rounded-xl border border-gray-100 bg-white p-4 shadow-sm">
              {listing.pictures.slice(0, 5).map((pic, i) => (
                <img
                  key={i}
                  src={pic.secure_url || pic.url}
                  alt={`Product ${i + 1}`}
                  className="h-24 w-24 rounded-lg border border-gray-100 object-cover"
                />
              ))}
            </div>
          )}

          {/* Basic info */}
          <div className="rounded-xl border border-gray-100 bg-white p-6 shadow-sm">
            <h2 className="mb-4 text-sm font-semibold text-gray-900">Listing Details</h2>
            <dl className="grid grid-cols-2 gap-4 text-sm">
              <div className="rounded-lg bg-gray-50 p-3">
                <dt className="text-xs font-medium text-gray-400">Price</dt>
                <dd className="mt-1 font-semibold text-gray-900">{formatCurrency(listing.price, listing.currency_id)}</dd>
              </div>
              <div className="rounded-lg bg-gray-50 p-3">
                <dt className="text-xs font-medium text-gray-400">Market</dt>
                <dd className="mt-1 font-semibold text-gray-900">{listing.site_id}</dd>
              </div>
              <div className="rounded-lg bg-gray-50 p-3">
                <dt className="text-xs font-medium text-gray-400">Category</dt>
                <dd className="mt-1 font-semibold text-gray-900">{listing.category_name || listing.category_id}</dd>
              </div>
              <div className="rounded-lg bg-gray-50 p-3">
                <dt className="text-xs font-medium text-gray-400">Status</dt>
                <dd className="mt-1 font-semibold capitalize text-gray-900">{listing.status}</dd>
              </div>
            </dl>
          </div>

          {/* Description */}
          {listing.description && (
            <div className="rounded-xl border border-gray-100 bg-white p-6 shadow-sm">
              <h2 className="mb-3 text-sm font-semibold text-gray-900">Description</h2>
              <p className="whitespace-pre-wrap text-sm leading-relaxed text-gray-600">{listing.description}</p>
            </div>
          )}

          {/* Attributes */}
          {listing.attributes && listing.attributes.length > 0 && (
            <div className="rounded-xl border border-gray-100 bg-white p-6 shadow-sm">
              <div className="mb-4 flex items-center justify-between">
                <h2 className="text-sm font-semibold text-gray-900">Attributes</h2>
                <button
                  onClick={handleOptimizeAttributes}
                  disabled={optimizing}
                  className="flex items-center gap-1.5 rounded-lg bg-brand-500 px-3 py-1.5 text-xs font-medium text-white hover:bg-brand-600 disabled:opacity-50"
                >
                  {optimizing ? (
                    <>
                      <span className="spinner h-3 w-3 border-white border-r-transparent" />
                      Analyzing...
                    </>
                  ) : (
                    <>
                      <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904 9 18.75l-.813-2.846a4.5 4.5 0 0 0-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 0 0 3.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 0 0 3.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 0 0-3.09 3.09Z" />
                      </svg>
                      Suggest Missing
                    </>
                  )}
                </button>
              </div>
              <div className="grid grid-cols-2 gap-2 text-sm">
                {listing.attributes.map((attr, i) => (
                  <div key={i} className="flex justify-between rounded-lg bg-gray-50 px-3 py-2.5">
                    <span className="text-gray-500">{attr.name}</span>
                    <span className={cn("font-medium", !attr.value_name ? "text-red-500" : "text-gray-900")}>
                      {attr.value_name || "Missing"}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Attribute Suggestions */}
          {attrOpt && attrOpt.suggestions.length > 0 && (
            <div className="rounded-xl border-2 border-brand-200 bg-brand-50 p-6">
              <h2 className="mb-3 text-sm font-semibold text-brand-800">
                <span className="mr-1.5 inline-block">AI Attribute Suggestions</span>
              </h2>
              <div className="space-y-3">
                {attrOpt.suggestions.map((s, i) => (
                  <div key={i} className="rounded-lg border border-brand-100 bg-white p-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-gray-900">{s.attribute_name}</span>
                      <span
                        className={cn(
                          "rounded-full px-2 py-0.5 text-xs font-medium",
                          s.confidence === "high"
                            ? "bg-green-50 text-green-700"
                            : s.confidence === "medium"
                              ? "bg-amber-50 text-amber-700"
                              : "bg-gray-100 text-gray-600"
                        )}
                      >
                        {s.confidence}
                      </span>
                    </div>
                    <p className="mt-1 text-sm font-medium text-brand-700">{s.suggested_value}</p>
                    <p className="mt-1 text-xs text-gray-500">{s.reasoning}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right column */}
        <div className="space-y-6">
          {/* Title Optimization */}
          <div className="rounded-xl border border-gray-100 bg-white p-6 shadow-sm">
            <h2 className="mb-3 text-sm font-semibold text-gray-900">Title Optimization</h2>
            <p className="mb-2 text-xs font-medium text-gray-400">Current title</p>
            <p className="mb-4 rounded-lg bg-gray-50 p-3 text-sm font-medium text-gray-700">{listing.title}</p>
            <button
              onClick={handleOptimizeTitle}
              disabled={optimizing}
              className="flex w-full items-center justify-center gap-2 rounded-lg bg-brand-500 px-4 py-2.5 text-sm font-semibold text-white hover:bg-brand-600 disabled:opacity-50"
            >
              {optimizing ? (
                <>
                  <span className="spinner border-white border-r-transparent" />
                  Generating...
                </>
              ) : (
                <>
                  <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904 9 18.75l-.813-2.846a4.5 4.5 0 0 0-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 0 0 3.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 0 0 3.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 0 0-3.09 3.09Z" />
                  </svg>
                  Generate Optimized Titles
                </>
              )}
            </button>

            {titleOpt && (
              <div className="mt-4 space-y-3">
                {titleOpt.variants.map((v, i) => (
                  <div key={i} className="rounded-lg border border-brand-200 bg-brand-50 p-3">
                    <p className="text-sm font-medium text-brand-900">{v.title}</p>
                    <p className="mt-1 text-xs text-gray-500">{v.reasoning}</p>
                    <button
                      onClick={() => handleApplyTitle(i)}
                      disabled={applying !== null}
                      className="mt-2 inline-flex items-center gap-1 rounded-lg bg-brand-600 px-3 py-1 text-xs font-medium text-white hover:bg-brand-700 disabled:opacity-50"
                    >
                      {applying === i ? (
                        <>
                          <span className="spinner h-3 w-3 border-white border-r-transparent" />
                          Applying...
                        </>
                      ) : (
                        "Apply to MeLi"
                      )}
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Competitors */}
          <div className="rounded-xl border border-gray-100 bg-white p-6 shadow-sm">
            <h2 className="mb-3 text-sm font-semibold text-gray-900">Top Competitors</h2>
            {competitors.length === 0 ? (
              <div className="py-4 text-center">
                <p className="text-sm text-gray-400">No competitors found</p>
              </div>
            ) : (
              <div className="space-y-3">
                {competitors.map((c, i) => (
                  <div key={i} className="rounded-lg bg-gray-50 p-3">
                    <p className="text-sm font-medium text-gray-900">{c.title}</p>
                    <div className="mt-1.5 flex items-center justify-between">
                      <span className="text-sm font-medium text-gray-600">
                        {formatCurrency(c.price, c.currency_id)}
                      </span>
                      <a
                        href={c.permalink}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 text-xs font-medium text-brand-600 hover:text-brand-700"
                      >
                        View
                        <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 6H5.25A2.25 2.25 0 0 0 3 8.25v10.5A2.25 2.25 0 0 0 5.25 21h10.5A2.25 2.25 0 0 0 18 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25" />
                        </svg>
                      </a>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
