# ISCOR AI Demo Data Handling

This demo database is designed for defense/prototype use, not production clinical deployment.

## Implemented Controls

- Unskippable consent is required before a screening can run.
- `/session` creates a short-lived session token and stores only a SHA-256 hash of the token.
- `/screen` and `/submit-screening` accept screening requests and optionally validate bearer session tokens.
- `/latest` returns the most recent report, including conversation history if present.
- `/history` returns recent saved screenings for a session token or for the demo dataset if no token is supplied.
- `/get-report/{screening_id}` returns a saved screening report by ID.
- `/chat` stores constrained Q&A exchanges linked to a screening.
- `SafetyEvents` records High-risk risk-gate interceptions.
- `purge_expired_sessions()` revokes expired sessions.
- `purge_old_screenings(retention_days=30)` deletes screening-linked records older than the retention window.
- Optional at-rest field protection is supported for raw answers, explanations, suggestions, questions, and Q&A responses.

## Optional Encryption

Set `ISCOR_DB_ENCRYPTION_KEY` to a Fernet key before starting the API:

```powershell
$env:ISCOR_DB_ENCRYPTION_KEY="<fernet-key>"
```

When configured, sensitive text fields are stored with a `fernet:` prefix and decrypted only by the application. Without this key, the demo stores those fields in plaintext and should not be described as encrypted.

## Retention Policy for the Report

For the submitted prototype, use a 30-day screening retention policy unless the evaluator asks for longer audit history. Expired sessions can be revoked immediately because they are not needed for model reproducibility.

## Remaining Production Gaps

- No role-based admin dashboard.
- No managed key rotation.
- No full database-level encryption.
- No institutional identity provider integration.
- No audit review workflow for a human counselor.
