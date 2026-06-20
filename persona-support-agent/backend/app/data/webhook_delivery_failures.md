# Webhook Delivery Failures

## Overview
Webhooks notify your server of events (e.g., payment.success, user.updated). This article covers delivery failures.

## Common Causes
- Endpoint returned a non-2xx status code.
- Endpoint timed out (>10 seconds).
- SSL certificate on the receiving endpoint is invalid or expired.

## Retry Policy
Failed webhooks are retried 5 times with exponential backoff (1m, 5m, 15m, 1h, 6h). After 5 failures, the webhook is marked as dead and an alert email is sent to the account admin.

## Resolution
1. Check your endpoint logs for the returned status code.
2. Ensure your endpoint responds within 10 seconds (process asynchronously if needed).
3. Renew SSL certificates before expiry.
4. Use the "Replay Webhook" button in the dashboard to manually retrigger a dead webhook.
