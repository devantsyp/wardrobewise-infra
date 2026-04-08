# Phase 1: Scaffolding and Auth - Context

**Gathered:** 2026-02-20
**Status:** Ready for planning

<domain>
## Phase Boundary

A running Django app deployed on Render with Tailwind CSS v4 styling, user registration/login/logout via email, session persistence, and a public landing page. Wardrobe CRUD, S3 storage, and AI features are separate phases.

</domain>

<decisions>
## Implementation Decisions

### Auth flow
- Registration: email + password only (no username)
- Confirm password field on registration form
- Login identifier: email only
- Separate pages for /register and /login with cross-links ("Don't have an account? Register" / "Already have an account? Log in")
- Auto-login after successful registration, redirect to wardrobe page (placeholder until Phase 2)
- Post-login redirect: wardrobe page
- Post-logout redirect: login page
- Immediate logout on click (no confirmation page)
- Always stay logged in — no "Remember me" checkbox, session persists until explicit logout
- Unauthenticated users accessing protected pages: redirect to login with return-to-original-page after login
- Unique emails enforced; explicit error: "An account with this email already exists"
- Django default password validators (length, common passwords, numeric-only, similarity)
- No forgot password flow — not needed for v1
- Dynamic nav links: Login/Register when logged out, user email + Logout when logged in
- Success flash messages after login, registration, and logout (Django messages framework)

### Login error handling
- Generic "Invalid email or password" on failed login (no enumeration of which field is wrong)
- Form clears all fields (including email) on failed submit
- No password show/hide toggle
- No button loading/disabled state on submit

### CSS framework & visual style
- Tailwind CSS v4 (latest)
- Bold & modern visual vibe — strong colors, sharp contrasts, confident feel
- Custom color palette with 5 families:
  - **Dark Teal:** #e9fafb → #051d1f (50–950)
  - **Deep Space Blue:** #e9f6fb → #05161f (50–950) — **PRIMARY brand color**
  - **Lilac Ash:** #f2f1f3 → #121013 (50–950)
  - **Thistle:** #f3f0f4 → #130f15 (50–950)
  - **Lavender:** #edecf8 → #0b091b (50–950)
- Color roles: Deep Space Blue = primary (buttons, links, nav accents); Lavender = hover/focus states; Dark Teal = success/positive; Thistle & Lilac Ash = muted/secondary text

### Base template & nav
- Top horizontal nav bar with light/white background and colored text/accents
- App name "Wardrobe Wise" as styled text (no icon/logo)
- Desktop-first layout (mobile responsiveness deferred)
- Page background: very light tint (one of the 50-shade palette colors)

### Landing page
- Hero section with CTA for logged-out users
- Hero copy: "Ready to make laundry a no-brainer?"
- No sub-heading — just hero copy then CTA button
- CTA button text: "Get Started" (links to register page)

### Error & validation UX
- Form validation on submit only (server-side, no JS validation)
- Inline errors below each field (red text, standard red color)
- Flash messages as top-right toast notifications with manual close (X button)
- User-friendly error message rewrites (plain English, not Django's raw defaults)
- Errors only — no green/success state on valid fields
- Default Django 404 and 500 error pages (custom pages deferred)
- No button loading states — standard form submission

### Claude's Discretion
- Exact Tailwind v4 setup method for Django (CDN vs build tool)
- Which palette 50-shade to use for page background tint
- Typography choices (font family, sizes, weights)
- Spacing and layout proportions
- Flash message toast animation/styling details
- Health check endpoint implementation
- Split settings structure (base/dev/prod)
- Render deployment configuration details

</decisions>

<specifics>
## Specific Ideas

- Hero copy is exactly: "Ready to make laundry a no-brainer?"
- CTA button text is exactly: "Get Started"
- The full custom color palette was provided with exact hex values for all 5 families (dark-teal, deep-space-blue, lilac-ash, thistle, lavender) at all shade levels (50–950)
- Bold & modern feel inspired by Vercel/Stripe aesthetic — strong color blocks, sharp contrasts

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 01-scaffolding-and-auth*
*Context gathered: 2026-02-20*
