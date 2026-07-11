-- EcoSaur Supabase Database Setup Schema
-- Run this in your Supabase SQL Editor to initialize production schemas and triggers.

-- 1. Create User Profiles Table linked to Supabase Auth users
create table public.profiles (
    id uuid references auth.users on delete cascade primary key,
    email text not null,
    health_mode text default 'General',
    created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Enable RLS on Profiles
alter table public.profiles enable row level security;

create policy "Users can view own profile" 
    on public.profiles for select 
    using (auth.uid() = id);

create policy "Users can update own profile" 
    on public.profiles for update 
    using (auth.uid() = id);

-- Trigger to automatically sync auth.users with public.profiles on signup
create or replace function public.handle_new_user()
returns trigger as $$
begin
    insert into public.profiles (id, email, health_mode)
    values (new.id, new.email, 'General');
    return new;
end;
$$ language plpgsql security definer;

create trigger on_auth_user_created
    after insert on auth.users
    for each row execute procedure public.handle_new_user();


-- 2. Create Scan History Table
create table public.scan_history (
    id uuid primary key default gen_random_uuid(),
    user_id uuid references public.profiles on delete cascade not null,
    corrected_text text not null,
    score integer not null,
    grade text not null,
    explanation text not null,
    alternative_name text,
    alternative_recipe text,
    alternative_prep_time integer,
    alternative_cost integer,
    breakdown_json text not null,
    confidence_ocr double precision default 1.0,
    confidence_match double precision default 1.0,
    confidence_analysis double precision default 1.0,
    confidence_rec double precision default 1.0,
    date timestamp with time zone default timezone('utc'::text, now()) not null,
    created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Enable RLS on Scan History
alter table public.scan_history enable row level security;

create policy "Users can view own scans" 
    on public.scan_history for select 
    using (auth.uid() = user_id);

create policy "Users can insert own scans" 
    on public.scan_history for insert 
    with check (auth.uid() = user_id);

create policy "Users can delete own scans" 
    on public.scan_history for delete 
    using (auth.uid() = user_id);


-- 3. Create API Usage Quota Limiting Table
create table public.api_usage (
    id uuid primary key default gen_random_uuid(),
    user_id uuid references public.profiles on delete cascade not null,
    scan_count integer default 0 not null,
    date date default current_date not null,
    constraint unique_user_date unique (user_id, date)
);

-- Enable RLS on API Usage
alter table public.api_usage enable row level security;

create policy "Users can view own api usage" 
    on public.api_usage for select 
    using (auth.uid() = user_id);
