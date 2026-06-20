# Network Allowlist Requirements

For integrations that require inbound connections from our platform (database sync, webhooks, VPC peering), allowlist the following IP ranges:

- 52.14.0.0/16 (primary sync connector)
- 34.201.0.0/16 (webhook delivery)
- 13.248.0.0/16 (backup region failover)

Ports: TCP 443 (HTTPS) and 5432/3306 (database sync only, optional).

Changes to allowlisted ranges are announced 30 days in advance via the status page and email to account admins.
