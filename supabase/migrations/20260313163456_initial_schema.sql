-- MeliOptimizer initial schema

-- gen_random_uuid() is built into Supabase/PostgreSQL 13+

-- Tenants (multi-tenant SaaS)
create table tenants (
  id uuid primary key default gen_random_uuid(),
  name varchar(255) not null,
  plan varchar(50) default 'free',
  created_at timestamptz default now()
);

-- Users
create table users (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references tenants(id) on delete cascade,
  email varchar(320) unique not null,
  password_hash varchar(255) not null,
  name varchar(255) not null,
  preferred_language varchar(5) default 'es',
  is_active boolean default true,
  created_at timestamptz default now()
);

create index idx_users_tenant_id on users(tenant_id);
create index idx_users_email on users(email);

-- Mercado Libre connected accounts
create table meli_accounts (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references tenants(id) on delete cascade,
  meli_user_id bigint unique not null,
  site_id varchar(5) not null,
  nickname varchar(255) default '',
  access_token varchar(512) not null,
  refresh_token varchar(512) not null,
  token_expires_at timestamptz not null,
  is_active boolean default true,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create index idx_meli_accounts_tenant_id on meli_accounts(tenant_id);
create index idx_meli_accounts_meli_user_id on meli_accounts(meli_user_id);

-- Listings
create table listings (
  id uuid primary key default gen_random_uuid(),
  meli_account_id uuid not null references meli_accounts(id) on delete cascade,
  meli_item_id varchar(20) unique not null,
  site_id varchar(5) not null,
  title varchar(255) not null,
  category_id varchar(30) default '',
  category_name varchar(255) default '',
  price float default 0,
  currency_id varchar(5) default 'ARS',
  status varchar(20) default 'active',
  description text,
  attributes jsonb,
  pictures jsonb,
  tags text[],
  quality_score integer,
  health_status varchar(20),
  attribute_completeness_pct float default 0,
  last_synced_at timestamptz,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create index idx_listings_meli_account_id on listings(meli_account_id);
create index idx_listings_meli_item_id on listings(meli_item_id);
create index idx_listings_site_id on listings(site_id);
create index idx_listings_status on listings(status);

-- Optimizations (AI suggestions)
create table optimizations (
  id uuid primary key default gen_random_uuid(),
  listing_id uuid not null references listings(id) on delete cascade,
  type varchar(20) not null,
  status varchar(20) default 'pending',
  original_title varchar(255),
  suggested_titles jsonb,
  original_description text,
  suggested_description text,
  suggested_attributes jsonb,
  model_version varchar(50) default 'claude-sonnet-4-20250514',
  prompt_version varchar(20) default 'v1',
  applied_at timestamptz,
  created_at timestamptz default now()
);

create index idx_optimizations_listing_id on optimizations(listing_id);

-- Row Level Security (disabled for now, app handles auth via JWT)
alter table tenants enable row level security;
alter table users enable row level security;
alter table meli_accounts enable row level security;
alter table listings enable row level security;
alter table optimizations enable row level security;
