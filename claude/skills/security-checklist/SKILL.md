---
name: security-checklist
description: Security checklist to follow WHILE building, for Next.js + Supabase + Netlify apps (e.g. Traksy, multi-tenant, student data). Use when adding or changing auth, sessions, roles, Server Actions, route handlers/API endpoints, Supabase tables/migrations/RLS policies/functions/storage, file uploads, forms or any user input, secrets/env vars, or anything touching personal data. Complements the built-in /security-review (which audits a finished diff).
---

# Security checklist (build-time)

Adapted 2026-09-21 from everything-claude-code's security-review, rewritten for this stack. Check the items that apply to what you are touching and say which ones you checked. Anything marked **STOP** is a blocker: fix it before continuing and tell {{NAME}}.

## 1. Secrets and keys
- Supabase anon/publishable key is public by design; all protection comes from RLS. The **service_role / secret key bypasses RLS**: server-only, never in a `NEXT_PUBLIC_*` var, never imported by a client component. **STOP** if it is.
- Anything `NEXT_PUBLIC_*` ships to the browser. Treat it as published.
- Secrets live in env vars (local `.env.local`, gitignored; production in Netlify env settings). Never in code, commits, logs, Brain notes or chat.
- Check before commit: `git diff --cached | grep -iE "(secret|service_role|sk_|api[_-]?key|password)"`. A secret that ever hit git history is compromised: tell {{NAME}} to rotate it.

## 2. Authentication (Supabase + Next.js)
- On the server, verify the user with `supabase.auth.getUser()` (or `getClaims()` where the project uses it). `getSession()` reads an unverified cookie: never base server-side authorization on it.
- Middleware is a convenience redirect, not the security boundary. Re-check auth in every Server Action, route handler and server component that reads protected data.
- Use the project's SSR cookie client (`@supabase/ssr`); don't copy tokens into `localStorage` or custom cookies.
- Don't change Supabase's cookie `SameSite=Lax` default to `Strict`: it breaks email-link/OAuth redirects.
- Admin and staff roles that can see student data across a school: require MFA (Supabase Auth TOTP, check `aal2` in the server-side role check), or flag to {{NAME}} if it is not in place yet.

## 3. Authorization and tenant isolation (most important for multi-tenant)
- **Every Server Action is a public POST endpoint.** Inside each one: authenticate, then check this user may do this action **on this tenant's/school's record**. Never trust IDs, tenant IDs or roles sent from the client.
- Tenant and role claims come from `app_metadata` (server-controlled) or a DB lookup. **Never `user_metadata`**: users can edit it themselves. **STOP** if authorization reads `user_metadata`.
- Default deny: a new route or action with no explicit check is a bug.
- Record IDs that appear in URLs or API responses are UUIDs (`gen_random_uuid()`), not sequential integers, so nobody can count or guess other schools' records. UUIDs don't replace the authorization check above; they only stop enumeration.

## 4. Row Level Security (every migration)
- `ALTER TABLE ... ENABLE ROW LEVEL SECURITY` on every table in an exposed schema (`public`), in the same migration that creates it. **STOP** if a new table ships without it.
- Policies per operation (`SELECT`, `INSERT`, `UPDATE`, `DELETE`), each scoped to the tenant: `USING (tenant_id = <tenant from JWT app_metadata or lookup>)`.
- `UPDATE` needs both `USING` and `WITH CHECK`, or users can move rows into another tenant. `INSERT` needs `WITH CHECK`.
- Wrap auth calls for performance: `(select auth.uid())`, `(select auth.jwt())`.
- Views bypass RLS unless created `WITH (security_invoker = true)`.
- `SECURITY DEFINER` functions bypass RLS: avoid them, or `SET search_path = ''`, check the caller's auth/tenant inside, and `REVOKE EXECUTE ... FROM public, anon` unless intended.
- Storage buckets need their own policies on `storage.objects` (tenant prefix in the path). Private buckets for anything with student data.
- Migrations are files only; no live DB writes (Traksy rule).
- **Test it:** for each new policy, query as a user from tenant A and confirm tenant B's rows are invisible and unwritable. Tests only, never against real data.

## 5. Input validation
- Validate every input on the server with a schema (zod or the project's existing validator): types, lengths, enums, formats. Client-side validation is UX only.
- Supabase query builder parameterises values. Danger zones: `.rpc()` into functions that build SQL strings, `.or()`/`.filter()` strings assembled from user input, raw SQL in functions. Never concatenate user input into SQL or filter strings.
- File uploads: check size, MIME type **and** extension server-side, generate the stored filename, and never trust the client's path.

## 6. XSS and output
- React escapes by default. `dangerouslySetInnerHTML` only with DOMPurify-sanitised content. **STOP** otherwise.
- User-supplied URLs in `href`/`src`: allow only `http:`/`https:` (block `javascript:` and `data:`).
- Newsletters, announcements and rich text are the XSS risk areas: sanitise on write or render, and pick one place consistently.
- Consider security headers (CSP, `X-Frame-Options`/`frame-ancestors`, `Referrer-Policy`) in `next.config` or `netlify.toml`.
- Third-party scripts from a CDN get an `integrity="sha384-..."` hash plus `crossorigin="anonymous"`, or are self-hosted. A changed upstream file then fails to load instead of running in your users' browsers.
- No public source maps in production (`productionBrowserSourceMaps` stays `false`; upload them privately to an error tracker if needed).

## 6b. Caching (Netlify CDN)
- Logged-in or per-user pages and API responses must never be stored by the CDN: `Cache-Control: private, no-store` (or rely on Next marking them dynamic because they read cookies). **STOP** if a page that shows student or school data is statically generated or CDN-cached without a per-user key.
- After deploying a change to caching, load a protected page as user A, then as user B or logged out, and confirm B never sees A's content.

## 7. CSRF
- Server Actions check `Origin` against `Host` automatically. Don't disable that (`serverActions.allowedOrigins` only for known proxies).
- Mutating route handlers that rely on cookies: accept only POST/PUT/PATCH/DELETE, and check the `Origin` header for anything sensitive.

## 8. Rate limiting and abuse
- Supabase Auth has built-in rate limits (and the default email sender is heavily limited; custom SMTP is needed for real use).
- In-memory rate limiters don't work on serverless (each instance has its own memory). Use platform rules (Netlify rate limiting) or a shared store (DB/Redis counter) for expensive or abusable endpoints: sign-up, invites, email sends, exports, search.
- Incoming webhooks (Stripe, email provider, Supabase): verify the signature with a constant-time compare, **and** reject events whose timestamp is older than ~5 minutes, and ignore event IDs already processed. A valid signature alone still allows replaying an old request.

## 9. Personal data (students are minors)
- Collect the minimum. No student names, emails or IDs in logs, analytics events, error trackers, URLs/query strings, or Brain notes.
- Logs never contain tokens, passwords, cookies, auth headers or magic-link URLs. Don't log whole request objects or headers; scrub these fields in any logger or error-tracker `beforeSend`.
- Errors to users are generic. Details go only to server logs, redacted. Never return `error.message`/stack from DB or auth errors to the client.
- Exports and bulk reads are scoped to the caller's tenant and role. Log who did them.
- Deleting or anonymising data needs {{NAME}}'s explicit sign-off.

## 10. Dependencies
- Commit the lockfile. `npm audit --omit=dev` before release. Don't add a package for something a few lines can do.
- GitHub Actions: pin third-party actions to a full commit SHA (`uses: owner/action@<40-char sha> # v4.1.0`), not a tag. Tags can be moved to malicious code.

## 11. Domains and DNS
- When a service is removed (old Netlify site, preview host, email provider), delete its DNS records in the same step. A record still pointing at a deleted service can be claimed by someone else to serve pages on your domain.

## Before calling a security-relevant change done
- [ ] Items above that apply were checked (list them)
- [ ] Cross-tenant test done for any new table, policy, action or endpoint
- [ ] No secrets in the diff; nothing server-only imported into client code
- [ ] For larger changes, suggest {{NAME}} run the built-in `/security-review` on the branch
