-- Add discovery source columns to tools table
-- Run this in Supabase SQL Editor

-- Add source tracking columns
ALTER TABLE tools ADD COLUMN IF NOT EXISTS source TEXT;
ALTER TABLE tools ADD COLUMN IF NOT EXISTS source_id TEXT;

-- Index for filtering by source
CREATE INDEX IF NOT EXISTS idx_tools_source ON tools(source);

-- Comment:
-- source: "product_hunt", "yc", "github", or NULL (for seeded tools)
-- source_id: ID from the source platform for deduplication
