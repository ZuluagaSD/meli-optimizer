import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatCurrency(amount: number, currency: string): string {
  const localeMap: Record<string, string> = {
    ARS: "es-AR",
    BRL: "pt-BR",
    MXN: "es-MX",
  };
  const locale = localeMap[currency] || "en-US";
  return new Intl.NumberFormat(locale, {
    style: "currency",
    currency,
  }).format(amount);
}

export function siteLabel(siteId: string): string {
  const labels: Record<string, string> = {
    MLA: "Argentina",
    MLB: "Brasil",
    MLM: "México",
  };
  return labels[siteId] || siteId;
}

export function healthColor(health: string | null): string {
  switch (health) {
    case "healthy":
      return "text-green-600 bg-green-50";
    case "warning":
      return "text-yellow-600 bg-yellow-50";
    case "critical":
      return "text-red-600 bg-red-50";
    default:
      return "text-gray-600 bg-gray-50";
  }
}

export function completenessColor(pct: number): string {
  if (pct >= 80) return "text-green-600";
  if (pct >= 50) return "text-yellow-600";
  return "text-red-600";
}
