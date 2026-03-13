const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

class ApiClient {
  private token: string | null = null;

  setToken(token: string) {
    this.token = token;
    if (typeof window !== "undefined") {
      localStorage.setItem("token", token);
    }
  }

  getToken(): string | null {
    if (!this.token && typeof window !== "undefined") {
      this.token = localStorage.getItem("token");
    }
    return this.token;
  }

  clearToken() {
    this.token = null;
    if (typeof window !== "undefined") {
      localStorage.removeItem("token");
    }
  }

  private async request<T>(
    path: string,
    options: RequestInit = {}
  ): Promise<T> {
    const token = this.getToken();
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...(options.headers as Record<string, string>),
    };
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    const res = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers,
    });

    if (res.status === 401) {
      this.clearToken();
      if (typeof window !== "undefined") {
        window.location.href = "/auth/login";
      }
      throw new Error("Unauthorized");
    }

    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body.detail || `API error: ${res.status}`);
    }

    return res.json();
  }

  // Auth
  async register(email: string, password: string, name: string) {
    const data = await this.request<{ access_token: string }>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password, name }),
    });
    this.setToken(data.access_token);
    return data;
  }

  async login(email: string, password: string) {
    const data = await this.request<{ access_token: string }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    this.setToken(data.access_token);
    return data;
  }

  getMeliAuthUrl(siteId: string) {
    return `${API_BASE}/auth/meli/authorize?site_id=${siteId}`;
  }

  async getMeliAccounts() {
    return this.request<MeliAccount[]>("/auth/meli/accounts");
  }

  async disconnectMeliAccount(accountId: string) {
    return this.request(`/auth/meli/disconnect/${accountId}`, { method: "POST" });
  }

  // Listings
  async syncListings(accountId: string) {
    return this.request<{ status: string; message: string }>(
      `/listings/sync/${accountId}`,
      { method: "POST" }
    );
  }

  async getListings(params: ListingsQuery = {}) {
    const searchParams = new URLSearchParams();
    if (params.site_id) searchParams.set("site_id", params.site_id);
    if (params.status) searchParams.set("status", params.status);
    if (params.health) searchParams.set("health", params.health);
    if (params.sort_by) searchParams.set("sort_by", params.sort_by);
    if (params.sort_order) searchParams.set("sort_order", params.sort_order);
    if (params.page) searchParams.set("page", String(params.page));
    if (params.page_size) searchParams.set("page_size", String(params.page_size));
    const qs = searchParams.toString();
    return this.request<PaginatedListings>(`/listings${qs ? `?${qs}` : ""}`);
  }

  async getListing(id: string) {
    return this.request<ListingDetail>(`/listings/${id}`);
  }

  async getCompetitors(listingId: string) {
    return this.request<Competitor[]>(`/listings/${listingId}/competitors`);
  }

  // Optimization
  async optimizeTitle(listingId: string) {
    return this.request<TitleOptimization>(`/optimize/title/${listingId}`, {
      method: "POST",
    });
  }

  async optimizeAttributes(listingId: string) {
    return this.request<AttributeOptimization>(`/optimize/attributes/${listingId}`, {
      method: "POST",
    });
  }

  async applyOptimization(optimizationId: string, selectedIndex: number = 0) {
    return this.request<{ status: string; message: string }>(
      `/optimize/${optimizationId}/apply?selected_index=${selectedIndex}`,
      { method: "POST" }
    );
  }

  async getOptimizationHistory(listingId: string) {
    return this.request<OptimizationHistory[]>(`/optimize/history/${listingId}`);
  }

  // Dashboard
  async getDashboardStats() {
    return this.request<DashboardStats>("/dashboard/stats");
  }
}

// Types

export interface MeliAccount {
  id: string;
  meli_user_id: number;
  site_id: string;
  nickname: string;
  is_active: boolean;
}

export interface ListingsQuery {
  site_id?: string;
  status?: string;
  health?: string;
  sort_by?: string;
  sort_order?: string;
  page?: number;
  page_size?: number;
}

export interface ListingSummary {
  id: string;
  meli_item_id: string;
  site_id: string;
  title: string;
  category_id: string;
  category_name: string;
  price: number;
  currency_id: string;
  status: string;
  health_status: string | null;
  attribute_completeness_pct: number;
  quality_score: number | null;
  last_synced_at: string | null;
}

export interface PaginatedListings {
  items: ListingSummary[];
  total: number;
  page: number;
  page_size: number;
}

export interface ListingDetail extends ListingSummary {
  description: string | null;
  attributes: Array<{ id: string; name: string; value_name: string | null }> | null;
  pictures: Array<{ url: string; secure_url: string }> | null;
  tags: string[] | null;
}

export interface Competitor {
  title: string;
  price: number;
  currency_id: string;
  permalink: string;
}

export interface TitleVariant {
  title: string;
  reasoning: string;
}

export interface TitleOptimization {
  optimization_id: string;
  original_title: string;
  variants: TitleVariant[];
}

export interface AttributeSuggestion {
  attribute_id: string;
  attribute_name: string;
  suggested_value: string;
  confidence: string;
  reasoning: string;
}

export interface AttributeOptimization {
  optimization_id: string;
  suggestions: AttributeSuggestion[];
}

export interface OptimizationHistory {
  id: string;
  type: string;
  status: string;
  original_title: string | null;
  suggested_titles: string[] | null;
  suggested_attributes: Record<string, unknown> | null;
  prompt_version: string;
  created_at: string;
}

export interface DashboardStats {
  total_listings: number;
  active_listings: number;
  paused_listings: number;
  avg_completeness: number;
  health_distribution: Record<string, number>;
  site_distribution: Record<string, number>;
  total_optimizations: number;
  applied_optimizations: number;
  listings_needing_attention: number;
}

export const api = new ApiClient();
