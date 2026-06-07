# Fix Error Log

Errors encountered during local setup and how they were resolved. Update this file when new environment or tooling issues are fixed.

---

## 1. Frontend has no `package.json` (dependencies could not install)

**Error details**

- Running `pnpm install` in `frontend/` failed with:
  ```
  [ERR_PNPM_NO_PKG_MANIFEST] No package.json found in C:\PythonProjects\document-copilot\frontend
  ```
- The `frontend/` folder only had `.env`, `.npmrc`, and `AGENTS.md` — the Vite app had not been scaffolded yet.
- User initially asked for "Python dependencies for frontend"; the frontend stack is **Node + pnpm**, not Python.

**Fix details**

- Scaffolded Vite + React + TypeScript in `frontend/` (per `docs/guides/frontend-setup.md`).
- Ran `pnpm install` and added core packages:
  - `react-router-dom`, `@supabase/supabase-js`
  - `tailwindcss`, `@tailwindcss/vite` (dev)
- Renamed package from `frontend-scaffold-temp` to `frontend` in `package.json`.

**Status:** Fixed

---

## 2. PowerShell `Unexpected token 'PS'`

**Error details**

```
At line:1 char:9
+ (.venv) PS C:\PythonProjects\document-copilot\frontend>corepack enabl ...
+         ~~
Unexpected token 'PS' in expression or statement.
```

- The full terminal line was pasted into PowerShell, including the prompt: `(.venv) PS C:\...\frontend>`.
- PowerShell tried to execute the prompt text as code; `PS` is not a valid token.

**Fix details**

- Run **only** the command — nothing before or after the `>`:
  ```powershell
  corepack enable
  ```
- Do not copy `(.venv)`, `PS`, or the path prefix when pasting from a terminal.

**Status:** Fixed (user workflow)

---

## 3. `corepack enable` — EPERM on Windows

**Error details**

```
Internal Error: EPERM: operation not permitted, open 'C:\Program Files\nodejs\pnpm'
Error: EPERM: operation not permitted, open 'C:\Program Files\nodejs\pnpm'
```

- `corepack enable` writes shim files into `C:\Program Files\nodejs\`, which requires **Administrator** rights on Windows.
- `pnpm` was not on PATH after a failed `corepack enable`.

**Fix details**

- Installed pnpm to the user-writable npm global directory (already on PATH):
  ```powershell
  npm install -g pnpm
  ```
- Verified: `pnpm --version` → `11.5.2`, located at `C:\Users\user\AppData\Roaming\npm\pnpm.cmd`.
- **Alternative (optional):** Open PowerShell as Administrator, then:
  ```powershell
  corepack enable
  corepack prepare pnpm@latest --activate
  ```
- Until admin `corepack enable` is run, use plain `pnpm` (not `corepack pnpm`).

**Status:** Fixed

---

## 4. shadcn init — Tailwind CSS not configured (v4)

**Error details**

```
✖ Validating Tailwind CSS. Found v4.
No Tailwind CSS configuration found at C:\PythonProjects\document-copilot\frontend.
It is likely you do not have Tailwind CSS installed or have an invalid configuration.
Install Tailwind CSS then try again.
```

- `tailwindcss` and `@tailwindcss/vite` were in `package.json` but not wired into the build.
- `vite.config.ts` had no Tailwind plugin.
- `src/index.css` had no `@import "tailwindcss";`.

**Fix details**

- Updated `frontend/vite.config.ts`:
  ```ts
  import tailwindcss from '@tailwindcss/vite'
  // plugins: [react(), tailwindcss()]
  ```
- Replaced `frontend/src/index.css` entry with:
  ```css
  @import "tailwindcss";
  ```
- Ran `pnpm dlx shadcn@latest init --defaults` (shadcn then appended theme imports to `index.css`).

**Files changed:** `frontend/vite.config.ts`, `frontend/src/index.css`

**Status:** Fixed

---

## 5. shadcn init — import alias `@/*` not found

**Error details**

```
✖ Validating import alias.
Could not find valid path aliases or package imports for init.
Configure path aliases in tsconfig.json or imports in package.json, then run init again.
```

- Vite’s split `tsconfig` had no `baseUrl` or `paths` for `@/*`.
- `vite.config.ts` had no `resolve.alias` for `@` → `./src`.

**Fix details**

- Added to `frontend/tsconfig.json` and `frontend/tsconfig.app.json`:
  ```json
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  }
  ```
- Added to `frontend/vite.config.ts`:
  ```ts
  import path from 'path'
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  }
  ```
- `@types/node` was already installed (required for `path` in Vite config).

**Files changed:** `frontend/tsconfig.json`, `frontend/tsconfig.app.json`, `frontend/vite.config.ts`

**Status:** Fixed

---

## 6. shadcn init — first run exited after dependency install

**Error details**

- Preflight checks passed (framework, Tailwind v4, alias).
- `pnpm add` for shadcn deps completed, but init exited with code 1:
  ```
  [ERR_PNPM_IGNORED_BUILDS] Ignored build scripts: msw@2.14.6
  Run "pnpm approve-builds" to pick which dependencies should be allowed to run scripts.
  ```
- `components.json` was written; `src/lib/utils.ts` and theme CSS were not created on the first run.

**Fix details**

- Re-ran init after config fixes:
  ```powershell
  cd frontend
  pnpm install
  pnpm dlx shadcn@latest init --defaults --force
  ```
- Second run completed: created `components.json`, `src/lib/utils.ts`, `src/components/ui/button.tsx`, and updated `src/index.css`.
- If build-script warnings recur: `pnpm approve-builds` in `frontend/`.

**Status:** Fixed

---

## 7. TypeScript `baseUrl` deprecation (TS5101)

**Error details**

```
tsconfig.json(8,5): error TS5101: Option 'baseUrl' is deprecated and will stop functioning in TypeScript 7.0.
```

- Appeared after adding `baseUrl` / `paths` to root `tsconfig.json` for shadcn alias validation (required by shadcn Vite guide).

**Fix details**

- Added to `frontend/tsconfig.json` `compilerOptions`:
  ```json
  "ignoreDeprecations": "6.0"
  ```
- `pnpm tsc --noEmit` passes.

**Files changed:** `frontend/tsconfig.json`

**Status:** Fixed

---

## 8. Root `uv sync` cleared workspace venv packages (side effect)

**Error details**

- Running `uv sync` at repo root (`document-copilot/pyproject.toml` has empty `dependencies`) uninstalled ~199 packages from the root `.venv`.
- Root `pyproject.toml` is a minimal stub; backend deps live in `backend/pyproject.toml`.

**Fix details**

- Use backend venv for API work:
  ```powershell
  cd backend
  uv sync
  ```
- Do not rely on root `uv sync` for backend dependencies.

**Status:** Documented — use `cd backend && uv sync`

---

## 9. Pylance: `supabase.lib.client_options` could not be resolved

**Error details**

```
Import "supabase.lib.client_options" could not be resolved
```

- Reported in `backend/app/database/supabase.py` when importing `SyncClientOptions` from an internal submodule:
  ```python
  from supabase.lib.client_options import SyncClientOptions
  ```
- Runtime worked (`uv run python` could import it), but Pylance/Pyright flags internal paths that are not part of the package’s public export surface.

**Fix details**

- Use the public top-level export instead (`SyncClientOptions` is re-exported as `ClientOptions`):
  ```python
  from supabase import Client, ClientOptions, create_client
  ```
- Replace `SyncClientOptions(...)` with `ClientOptions(...)` — same sync client options type.

**Files changed:** `backend/app/database/supabase.py`

**Status:** Fixed

---

## Quick reference

| Symptom | Command / action |
| -------- | ---------------- |
| No `package.json` in frontend | Scaffold per `docs/guides/frontend-setup.md`, then `pnpm install` |
| `Unexpected token 'PS'` | Paste only the command, not the terminal prompt |
| `corepack enable` EPERM | `npm install -g pnpm` (no admin) |
| shadcn Tailwind / alias errors | Wire Tailwind v4 + `@/*` alias (see errors 4–5 above) |
| shadcn init incomplete | `pnpm dlx shadcn@latest init --defaults --force` |
| Backend Python deps | `cd backend && uv sync` |
| Pylance unresolved `supabase.lib.*` | Import `ClientOptions` from `supabase`, not internal submodules |

**Last updated:** 2026-06-07
