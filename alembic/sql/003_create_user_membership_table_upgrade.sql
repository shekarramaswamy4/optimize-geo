-- Create user_membership table
CREATE TABLE IF NOT EXISTS user_membership (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    entity_id UUID NOT NULL REFERENCES entity(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL DEFAULT 'member',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by UUID,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_by UUID,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    
    -- Ensure unique membership per user/entity combination
    CONSTRAINT unique_user_entity_membership UNIQUE (user_id, entity_id)
);

-- Create indexes
CREATE INDEX idx_user_membership_user_id ON user_membership(user_id);
CREATE INDEX idx_user_membership_entity_id ON user_membership(entity_id);
CREATE INDEX idx_user_membership_role ON user_membership(role);
CREATE INDEX idx_user_membership_is_active ON user_membership(is_active);

-- Create trigger for updated_at
CREATE TRIGGER update_user_membership_updated_at BEFORE UPDATE ON user_membership
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();