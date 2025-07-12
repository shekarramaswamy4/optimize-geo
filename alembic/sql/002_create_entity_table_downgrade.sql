-- Drop entity table and related objects
DROP TRIGGER IF EXISTS update_entity_updated_at ON entity;
DROP TABLE IF EXISTS entity CASCADE;