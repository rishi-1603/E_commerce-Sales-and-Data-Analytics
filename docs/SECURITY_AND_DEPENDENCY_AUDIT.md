# SECURITY & DEPENDENCY AUDIT — E-Commerce
### Audit date: 2026-10-17

## Dependencies (requirements.txt — exact pins)
pandas==2.2.3 · numpy==2.3.5 · scikit-learn==1.6.1 · scipy==1.17.1 ·
statsmodels==0.15.0 · matplotlib==3.10.9 · seaborn==0.13.2 · pytest==9.0.3
- Exact pins: reproducible builds; same versions in CI and local.
- No heavy/unnecessary stacks (no deep-learning frameworks).

## Secrets
- Scan of all tracked files for token patterns (github_pat_, ghp_, AWS keys,
  sk-...): **CLEAN** (2026-10-17).
- The maintainer's GitHub PAT exists only as an environment variable for pushes
  and is scheduled for rotation. It is NOT in this repository, its history,
  reports, or logs.

## Supply chain / CI
- CI runs on GitHub-hosted runners with the pinned versions above.
- No third-party actions beyond official ones (checkout, setup-python).
- Static dashboard: no server, no database, no auth surface -> minimal attack area.

## Data ethics
Synthetic dataset only; no personal data; claims scoped accordingly.

## Residual risks (honest)
- Dependency CVEs over time (pinned versions age): re-pin periodically.
- GitHub account security (2FA, PAT rotation) is the user's responsibility.
