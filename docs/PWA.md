# DSAapp — Progressive Web App (PWA) & Offline Shell Architecture

This document details the service worker lifecycle, offline caching strategies, security boundaries, and installation UX implemented in **Phase 9**.

---

## 1. PWA Architectural Overview

DSAapp is configured as a standalone Progressive Web App compliant with modern W3C Web App Manifest and Service Worker specifications. The platform offers desktop and mobile users:
- **Instant App Installation**: Add to Home Screen / Desktop Application wrapper without an app store middleman.
- **Offline Resilience**: Instant application shell loading even during intermittent connectivity or complete network loss.
- **Fast Static Asset Delivery**: Sub-10ms cache-first asset loading for scripts, stylesheets, and fonts.
- **Automatic Background Updates**: Seamless update detection with user-prompted cache invalidation.

---

## 2. Web App Manifest Specifications

The web application manifest is served from `/manifest.json` with the following parameters:
- **`name`**: `DSAapp — Advanced Coding & Online Judge Platform`
- **`short_name`**: `DSAapp`
- **`start_url`**: `/`
- **`display`**: `standalone` (removes browser URL bar, providing a native app container)
- **`theme_color`**: `#3b82f6` (brand primary blue)
- **`background_color`**: `#090d16` (slate-950 dark theme)
- **`icons`**: Maskable high-resolution PNG icons (192x192 and 512x512)
- **`shortcuts`**: Fast app actions for Quick Practice (`/practice`), Live Contests (`/contests`), and Revision (`/revision`).

---

## 3. Service Worker Strategy & Security Boundaries

The service worker is implemented in `frontend/public/sw.js` with strict security boundaries protecting private student and judge data.

### Caching Strategies
```
                       [Incoming Request]
                               │
            ┌──────────────────┴──────────────────┐
            ▼                                     ▼
    [Sensitive Endpoint?]                [Static Asset or Page?]
  - Starts with /api/                      - .js, .css, .woff2, .png
  - Starts with /health                    - HTML navigation (mode: navigate)
  - Contains /auth/, /judge/                      │
  - Contains /payments/, /admin/                  ▼
            │                            [Cache Strategy]
            ▼                             - Static: Cache-First
     [NETWORK ONLY]                       - Navigate: Network-First with
(Never stored in browser cache)             fallback to cached index.html
```

### Strict Security Invariants
1. **Network-Only for Sensitive APIs**: The service worker explicitly excludes and never intercepts requests matching `/api/`, `/health`, `/auth/`, `/payments/`, `/judge/`, or `/admin/`.
2. **Zero Credential Caching**: JWT access tokens, session cookies, payment orders, student code submissions, and admin telemetry are never cached in `caches` storage.
3. **Cache Versioning (`CACHE_NAME = 'dsaapp-shell-v1'`)**: Ensures clean cache evacuation on subsequent platform releases through the `activate` event listener.
4. **Offline Shell Fallback**: Navigation requests that encounter network errors fall back to the cached `index.html` application shell, presenting an offline state without displaying browser dinosaur screens.

---

## 4. Install & Update User Experience

### Installation Banner (`InstallPrompt.tsx`)
- Listens to the browser's `beforeinstallprompt` event.
- Displays a non-intrusive floating banner: *"Install DSAapp — Offline practice, faster loads, full desktop experience"*.
- Triggering "Install" executes the native OS installation flow.
- A dismissal action hides the prompt for the current session.

### Update Toast (`PwaUpdateToast.tsx`)
- Detects when a new service worker version has completed downloading in the background.
- Renders an alert toast: *"App Update Available — A new version of DSAapp has been downloaded"*.
- Clicking "Update Now" sends `SKIP_WAITING` to the waiting worker and reloads the page to activate the latest features immediately.
