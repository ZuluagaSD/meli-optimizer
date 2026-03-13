-- Change tags column from text[] to jsonb for SQLAlchemy JSON compatibility
ALTER TABLE listings ALTER COLUMN tags TYPE jsonb USING to_jsonb(tags);
