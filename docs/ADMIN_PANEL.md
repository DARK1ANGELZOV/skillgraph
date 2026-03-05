# Admin Panel

## Personas

- OWNER: full control, invites, billing view, analytics.
- HR_SENIOR: hiring operations + analytics.
- HR_JUNIOR: hiring operations.
- SUPERVISOR: read-only reports and executive summary.

## Views

- Login/Register Owner
- Dashboard (KPIs, vacancy creation, candidate invite)
- Interviews list and scores
- Analytics reports
- Settings (company info, invites, billing scaffold)

## UX

- Responsive layout for desktop and tablet/mobile.
- Light and dark themes.
- Animated glassmorphism-style surfaces.
- Clear distinction of primary and destructive actions.

## Integration

Admin app uses cookie-based auth and calls API endpoints with `credentials: include`.
