-- Run once in the SQL Editor of a dedicated FoodLink Supabase project.
-- Keep this schema OUT of Supabase Data API exposed schemas.
-- Django connects server-side; no Supabase API key or Supabase Auth is used.
CREATE SCHEMA IF NOT EXISTS foodlink;
REVOKE ALL ON SCHEMA foodlink FROM PUBLIC;
REVOKE ALL ON SCHEMA foodlink FROM anon, authenticated;
