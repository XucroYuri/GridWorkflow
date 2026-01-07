# EVIDENCE_WP-GW-09 (Auth & Supabase)

## 1. Frontend Integration

- **Supabase Client**: Configured in `frontend/src/lib/supabase.ts` using `import.meta.env`.
- **Auth Context**: Implemented in `frontend/src/contexts/AuthContext.tsx`.
- **Login UI**: Created `frontend/src/components/Auth/Login.tsx` (Magic Link).
- **Protection**: `App.tsx` wrapped with `AuthProvider` and `ProtectedRoute`.
- **API Client**: `frontend/src/services/apiClient.ts` intercepts requests to add Bearer token from Supabase session.

## 2. Backend Integration

- **Dependencies**: Added `gotrue`, `postgrest`, `pyjwt` to `backend/requirements.txt`.
- **Auth Middleware**: Codex implemented `backend/app/core/auth.py` with `require_user` dependency.
- **Route Protection**: `workflow.py`, `video.py`, `media.py` are protected via `APIRouter(dependencies=[Depends(require_user)])`.
- **JWT Validation**: Validates HS256 signature using `SUPABASE_JWT_SECRET`. Extracts `user_id`.

## 3. Database & RLS

- **SQL Schema**: [WP-GW-09_SUPABASE_RLS.sql](evidence/WP-GW-09_SUPABASE_RLS.sql)
- **Tables**: `tasks`, `media` with `user_id` foreign key.
- **RLS Policies**: Enforce `auth.uid() = user_id` for all operations.

## 4. Verification

- Frontend requires login to access `/` (redirects to Login).
- Backend returns 401/403 if Token is missing or invalid.
- Data isolation ensured by RLS policies at database level.

## 5. Security Review (Claude)

**Status: PASSED**

Performed a security audit of the implementation on 2026-01-07.

### Audit Method
- Static Code Analysis of Backend (`auth.py`, `main.py`, Routes) and Frontend (`supabase.ts`, `apiClient.ts`).
- Automated JWT Validation Testing (Backend).

### Key Findings
1.  **Authentication Flow**: Correctly implemented. Frontend securely retrieves session token and attaches it as `Bearer` header.
2.  **JWT Validation**: Backend `auth.py` correctly enforces HS256 signature verification using `SUPABASE_JWT_SECRET`.
    -   *Verified*: Rejects invalid signatures.
    -   *Verified*: Rejects expired tokens.
    -   *Verified*: Rejects mismatched audience (if configured).
3.  **Route Protection**: `require_user` dependency is correctly applied to all sensitive routers (`workflow`, `video`, `media`).
4.  **Data Isolation**: RLS policies in `WP-GW-09_SUPABASE_RLS.sql` correctly restrict access to `auth.uid() = user_id`.
    -   *Note*: Python backend currently does not write to these tables (uses external AI providers directly), but the infrastructure is ready for future persistence.

### Recommendations
-   **Environment Variables**: Ensure `SUPABASE_JWT_SECRET` is correctly set in the production environment.
-   **Dependency Cleanup**: `postgrest` is included in `backend/requirements.txt` but not yet used by the Python code. Retain if planned for immediate future use.
