# Provenance verification

PROVENANCE_VERIFICATION_PASS

Only CRLF/CR/LF line endings are canonicalized to LF. Every historical raw hash must match current bytes or a reproduced LF/CRLF encoding. Original payloads are untouched; canonical keys/implementation/settings hashes are separate sidecar fields in provenance_audit.json. Unknown implementation hashes, missing identity fields, altered settings or corrupt cache keys fail closed. Candidate loading now requires verified settings and exact nu/VA metadata. Objective reuse requires a separate scientific code/config/channel identity; old rows are adopted only through the hash-bound independent audit.
