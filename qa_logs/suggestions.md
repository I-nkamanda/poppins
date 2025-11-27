# QA Suggestions & Bug Report

## ✅ Resolved: Objective Generation Failed

**Severity**: High
**Component**: Frontend API Configuration
**Resolution**: Fixed Port Mismatch

### Issue Description
The application failed to generate learning objectives because the frontend was trying to communicate with the backend on port `8002`, while the backend was running on port `8001`.

### Resolution Steps
1. Identified `API_BASE_URL` in `frontend/src/services/api.ts` was set to `http://localhost:8002`.
2. Updated `API_BASE_URL` to `http://localhost:8001`.
3. Restarted frontend and backend servers.
4. Verified successful generation of objectives, course, and chapter content.

### Verification
- **Test Run**: Full Web Test Record Run (Retry 3)
- **Status**: Passed
- **Artifacts**: See `test_run_summary.md` for recordings and screenshots.

### Recommendations
- Ensure environment variables are used for API URLs in production to avoid hardcoded port mismatches.
