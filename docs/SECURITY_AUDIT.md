# Security audit scope

2026-10-30. This is a bounded portfolio audit, not a penetration-test certificate.

- Requirements-based dependency scan and selected historical/current secret signatures were checked in the preceding audit. They do not guarantee absence of every secret or vulnerability.
- No credential is needed for the deterministic dashboard and benchmark paths. External AI-provider checks are blocked when provider credentials are unavailable.
- Credential exposure cannot be repaired by deleting a repository file: rotate/revoke the exposed credential at its issuer.
- Source/configuration and regression checks were rerun after the reviewed PR integration. Main-branch CI remains the release gate.

## Project-specific repairs

- No shipped fixed SECRET_KEY fallback: a missing key creates a per-process ephemeral development key. Set a stable, strong key for any real deployment.
- Compose requires explicit POSTGRES_PASSWORD and SECRET_KEY. Example values are placeholders, not usable production credentials. Docker daemon/build execution was unavailable; no container-runtime certification is claimed.
- API tests always select a temporary database before settings/engines load, preventing test writes into a configured development/production database.
- SQL guard rejects mutating/multiple statements and non-whitelisted/qualified tables; oversized integer limits are capped at 100 and negative/dynamic limits rejected. This is not a proof against every expensive SELECT or a full resource-isolation policy.
