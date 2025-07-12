# API Authentication

The LumaRank API uses header-based authentication to secure endpoints and track user activity. The system integrates with WorkOS for automatic user provisioning.

## Authentication Method

All authenticated endpoints require three headers:

- `x-email`: User's email address
- `x-auth-id`: User's authentication ID from WorkOS
- `x-entity-id`: The entity (organization) ID the user is accessing

## Example Request

```bash
curl -X POST https://api.lumarank.com/api/v1/analyze \
  -H "Content-Type: application/json" \
  -H "x-email: user@example.com" \
  -H "x-auth-id: auth_01234567890" \
  -H "x-entity-id: 550e8400-e29b-41d4-a716-446655440000" \
  -d '{
    "website_url": "https://example.com",
    "test_questions": true
  }'
```

## Authentication Flow

### Session Context

Every authenticated request creates a complete session context that includes:

1. **User Context**: The authenticated user's information
2. **Entity Context**: The organization/entity being accessed
3. **Membership Context**: The user's role and permissions within the entity

The API validates that:
- The user exists (or is created from WorkOS)
- The entity exists and is active
- The user has an active membership in the entity

### Automatic User Provisioning

When a request is made with valid WorkOS authentication headers, the API will:

1. **Check Local Database**: First check if the user exists in the local database
2. **Query WorkOS**: If user not found locally, verify credentials with WorkOS
3. **Create User**: Automatically create a new user record from WorkOS data
4. **Verify Entity Access**: Check that the user has membership in the requested entity

This means users authenticated through your NextJS frontend (via WorkOS) will automatically have access to the API without manual registration, but they must have valid entity membership.

### Manual Registration (Optional)

You can still manually register users if needed:
```bash
POST /api/v1/auth/register
{
  "email": "user@example.com",
  "auth_id": "auth_01234567890",
  "first_name": "John",
  "last_name": "Doe"
}
```

### Checking Authentication Status

```bash
GET /api/v1/auth/check
Headers: x-email, x-auth-id, x-entity-id
```

## Endpoints

### Public Endpoints (No Authentication Required)

- `GET /health` - Health check
- `GET /readiness` - Readiness check
- `GET /metrics` - Prometheus metrics (if enabled)

### Authentication Endpoints

#### Check Authentication Status
```
GET /api/v1/auth/check
```

Returns whether the current request is authenticated and user info if available.

**Response:**
```json
{
  "success": true,
  "authenticated": true,
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "auth_id": "auth_01234567890",
    "first_name": "John",
    "last_name": "Doe",
    "is_active": true
  }
}
```

#### Get Current User
```
GET /api/v1/auth/me
Headers: x-email, x-auth-id
```

Returns the current authenticated user's information.

**Response:**
```json
{
  "success": true,
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "auth_id": "auth_01234567890",
    "first_name": "John",
    "last_name": "Doe",
    "is_active": true
  }
}
```

#### Register User
```
POST /api/v1/auth/register
```

Creates a new user account or updates existing user's auth_id.

**Request:**
```json
{
  "email": "user@example.com",
  "auth_id": "auth_01234567890",
  "first_name": "John",
  "last_name": "Doe"
}
```

### Protected Endpoints (Authentication Required)

All analyzer endpoints require authentication:

- `POST /api/v1/analyze` - Full website analysis
- `POST /api/v1/analyze/quick` - Quick analysis without testing
- `POST /api/v1/test-questions` - Test pre-generated questions

## Error Responses

### Missing Authentication Headers
```json
{
  "detail": "Missing authentication headers (x-email, x-auth-id, and x-entity-id required)"
}
```
Status Code: 401

### Invalid Entity ID Format
```json
{
  "detail": "Invalid entity ID format"
}
```
Status Code: 400

### Entity Not Found
```json
{
  "detail": "Entity not found"
}
```
Status Code: 404

### Access Denied to Entity
```json
{
  "detail": "Access denied to this entity"
}
```
Status Code: 403

### Invalid Credentials
```json
{
  "detail": "Invalid authentication credentials"
}
```
Status Code: 401

### User Not Found
```json
{
  "detail": "Invalid authentication credentials"
}
```
Status Code: 401

## Session Context Details

When authenticated, the API creates a complete session that includes:

### User Context
- User ID and email
- First and last name
- Authentication status

### Entity Context
- Entity ID and name
- Entity active status

### Membership Context
- Membership ID
- User's role in the entity (member, admin, owner)
- Role-based permissions

### Data Attribution
All data created through the API is attributed to:
- The authenticated user (created_by)
- The entity context (entity_id)
- Request tracking ID for correlation

## Security Best Practices

1. **HTTPS Only**: Always use HTTPS in production
2. **Token Rotation**: Regularly rotate auth_ids through your auth provider
3. **Rate Limiting**: API has built-in rate limiting per user
4. **Audit Logging**: All authenticated actions are logged

## Integration Example

### JavaScript/TypeScript
```typescript
const headers = {
  'Content-Type': 'application/json',
  'x-email': userEmail,
  'x-auth-id': userAuthId,
  'x-entity-id': entityId,
};

const response = await fetch('https://api.lumarank.com/api/v1/analyze', {
  method: 'POST',
  headers,
  body: JSON.stringify({
    website_url: 'https://example.com',
    test_questions: true,
  }),
});
```

### Python
```python
import requests

headers = {
    'x-email': user_email,
    'x-auth-id': user_auth_id,
    'x-entity-id': entity_id,
}

response = requests.post(
    'https://api.lumarank.com/api/v1/analyze',
    headers=headers,
    json={
        'website_url': 'https://example.com',
        'test_questions': True,
    }
)
```

## Testing Authentication

### With WorkOS Integration

For testing with actual WorkOS integration:

1. Set up WorkOS credentials in `.env`:
   ```bash
   WORKOS_API_KEY=sk_test_your_key_here
   WORKOS_CLIENT_ID=client_your_id_here
   ```

2. Use valid WorkOS user credentials from your NextJS app

### Without WorkOS (Local Testing)

For local development without WorkOS:

1. Start the databases:
   ```bash
   make db-up
   ```

2. Create a test user via SQL:
   ```sql
   INSERT INTO users (email, first_name, last_name, workos_user_id)
   VALUES ('test@example.com', 'Test', 'User', 'test_auth_123');
   ```

3. Create test entity and membership:
   ```sql
   -- Create test entity
   INSERT INTO entity (id, name)
   VALUES ('550e8400-e29b-41d4-a716-446655440000', 'Test Organization');
   
   -- Create membership (get user ID from users table)
   INSERT INTO user_membership (user_id, entity_id, role)
   SELECT u.id, '550e8400-e29b-41d4-a716-446655440000', 'admin'
   FROM users u WHERE u.email = 'test@example.com';
   ```

4. Use these headers for testing:
   - `x-email: test@example.com`
   - `x-auth-id: test_auth_123`
   - `x-entity-id: 550e8400-e29b-41d4-a716-446655440000`

## WorkOS Integration Details

The API automatically integrates with WorkOS to:

- Verify user authentication
- Fetch user profile data (name, email)
- Create local user records on first access
- Maintain consistency between WorkOS and local data

This eliminates the need for separate user registration flows when users are already authenticated through your NextJS frontend.