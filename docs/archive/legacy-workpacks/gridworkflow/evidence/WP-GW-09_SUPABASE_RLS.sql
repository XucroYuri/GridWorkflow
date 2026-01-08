-- WP-GW-09_SUPABASE_RLS.sql
-- Supabase Schema and RLS Policies

-- 1. Create tasks table
create table if not exists public.tasks (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references auth.users(id) not null,
  title text,
  status text default 'pending',
  request_payload jsonb,
  response_payload jsonb,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

alter table public.tasks enable row level security;

-- 2. Create media table
create table if not exists public.media (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references auth.users(id) not null,
  file_url text not null,
  media_type text check (media_type in ('image', 'video')),
  task_id uuid references public.tasks(id),
  created_at timestamptz default now()
);

alter table public.media enable row level security;

-- 3. RLS Policies

-- Tasks Policies
create policy "Users can view their own tasks"
  on public.tasks for select
  using (auth.uid() = user_id);

create policy "Users can insert their own tasks"
  on public.tasks for insert
  with check (auth.uid() = user_id);

create policy "Users can update their own tasks"
  on public.tasks for update
  using (auth.uid() = user_id);

create policy "Users can delete their own tasks"
  on public.tasks for delete
  using (auth.uid() = user_id);

-- Media Policies
create policy "Users can view their own media"
  on public.media for select
  using (auth.uid() = user_id);

create policy "Users can insert their own media"
  on public.media for insert
  with check (auth.uid() = user_id);

-- 4. Helper function for updating updated_at
create or replace function update_updated_at_column()
returns trigger as $$
begin
    new.updated_at = now();
    return new;
end;
$$ language 'plpgsql';

create trigger update_tasks_updated_at
before update on public.tasks
for each row execute procedure update_updated_at_column();

