-- Drop user_membership table and related objects
DROP TRIGGER IF EXISTS update_user_membership_updated_at ON user_membership;
DROP TABLE IF EXISTS user_membership CASCADE;