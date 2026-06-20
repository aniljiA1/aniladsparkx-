# Database Integration Error Codes

## Overview
This article documents common internal error codes returned by our database integration connector (used for syncing customer data via the /v1/sync endpoint).

## Error Codes
- **DB_CONN_TIMEOUT**: Connection to the customer's database exceeded the 30-second timeout. Usually caused by firewall rules blocking our IP range (see Network Allowlist doc).
- **DB_SCHEMA_MISMATCH**: The target table schema does not match the expected sync schema version. Run `sync --validate-schema` to see the diff.
- **DB_AUTH_FAILED**: Provided database credentials are invalid or the user lacks SELECT/INSERT privileges on the sync schema.
- **DB_DEADLOCK_DETECTED**: Concurrent writes caused a deadlock; the connector automatically retries up to 3 times with exponential backoff.

## Step-by-Step Resolution
1. Check connector logs at `/var/log/sync-connector/error.log` for the specific error code.
2. For DB_CONN_TIMEOUT: whitelist IP range 52.14.0.0/16 in your firewall.
3. For DB_SCHEMA_MISMATCH: run schema migration scripts provided in the connector changelog.
4. For DB_AUTH_FAILED: regenerate a service account with correct grants.
5. If errors persist after these steps, collect the full log output and escalate to engineering support.
