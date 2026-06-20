# API Authentication Troubleshooting

## Overview
This article covers common API authentication errors when integrating with our REST API, including 401 and 403 responses.

## Authentication Method
All API requests require a Bearer token in the Authorization header:
```
Authorization: Bearer <API_KEY>
```
Tokens are generated in Account Settings > Developer > API Keys and expire after 90 days.

## Error: 401 Unauthorized
Causes:
- The API key is expired or revoked.
- The Authorization header is missing or malformed (must start with "Bearer ").
- Clock skew greater than 5 minutes between client and server causes signed request rejection.

Resolution:
1. Regenerate a new API key from the developer dashboard.
2. Verify the header format exactly matches `Bearer <key>` with a single space.
3. Sync server clock via NTP if using signed requests.

## Error: 403 Forbidden
Causes:
- The API key does not have the required scope/permission for the endpoint.
- IP allowlist restrictions are enabled and the request origin is not whitelisted.

Resolution:
1. Check the key's assigned scopes under Developer Settings.
2. Add the calling server's IP to the allowlist if IP restriction is enabled.

## Rate Limiting
API requests are limited to 100 requests/minute per key. Exceeding this returns a 429 status with a `Retry-After` header.
