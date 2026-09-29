import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, act } from '@testing-library/react';
import { InstallPrompt } from '../components/common/InstallPrompt';
import { PwaUpdateToast } from '../components/common/PwaUpdateToast';
import * as registerSwModule from '../pwa/registerSw';
import fs from 'fs';
import path from 'path';

describe('DSAapp Phase 9 PWA & Offline Engine', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Web App Manifest Verification', () => {
    it('verifies manifest.json exists, is valid JSON, and defines standalone PWA parameters', () => {
      const manifestPath = path.resolve(__dirname, '../../public/manifest.json');
      expect(fs.existsSync(manifestPath)).toBe(true);

      const raw = fs.readFileSync(manifestPath, 'utf-8');
      const manifest = JSON.parse(raw);

      expect(manifest.name).toContain('DSAapp');
      expect(manifest.short_name).toBe('DSAapp');
      expect(manifest.display).toBe('standalone');
      expect(manifest.theme_color).toBe('#3b82f6');
      expect(manifest.background_color).toBe('#090d16');
      expect(manifest.start_url).toBe('/');
      expect(Array.isArray(manifest.icons)).toBe(true);
      expect(manifest.icons.length).toBeGreaterThan(0);

      // Verify shortcuts
      expect(Array.isArray(manifest.shortcuts)).toBe(true);
      const practiceShortcut = manifest.shortcuts.find((s: any) => s.url === '/practice');
      expect(practiceShortcut).toBeDefined();
    });
  });

  describe('Service Worker (sw.js) Architecture & Security Boundaries', () => {
    it('verifies sw.js exists and implements Cache-First static assets and Network-Only security rules', () => {
      const swPath = path.resolve(__dirname, '../../public/sw.js');
      expect(fs.existsSync(swPath)).toBe(true);

      const swContent = fs.readFileSync(swPath, 'utf-8');

      // Verify versioning and cache identifier
      expect(swContent).toContain('CACHE_NAME');
      expect(swContent).toContain('dsaapp-shell-v1');

      // Verify explicit Network-Only bypass for sensitive endpoints
      expect(swContent).toContain('/api/');
      expect(swContent).toContain('/health');
      expect(swContent).toContain('/auth/');
      expect(swContent).toContain('/payments/');
      expect(swContent).toContain('/judge/');
      expect(swContent).toContain('/admin/');

      // Verify offline shell fallback
      expect(swContent).toContain('/index.html');
      expect(swContent).toContain('caches.match');
    });
  });

  describe('InstallPrompt Component', () => {
    it('does not render when app is not installable', () => {
      vi.spyOn(registerSwModule, 'usePwa').mockReturnValue({
        isInstallable: false,
        isOnline: true,
        updateAvailable: false,
        triggerInstall: vi.fn(),
        applyUpdate: vi.fn(),
      });

      const { container } = render(<InstallPrompt />);
      expect(container.firstChild).toBeNull();
    });

    it('renders banner when installable and invokes triggerInstall on click', () => {
      const triggerInstall = vi.fn();
      vi.spyOn(registerSwModule, 'usePwa').mockReturnValue({
        isInstallable: true,
        isOnline: true,
        updateAvailable: false,
        triggerInstall,
        applyUpdate: vi.fn(),
      });

      render(<InstallPrompt />);

      expect(screen.getByText('Install DSAapp')).toBeInTheDocument();
      expect(screen.getByText(/Offline practice, faster loads/i)).toBeInTheDocument();

      const installBtn = screen.getByRole('button', { name: 'Install' });
      fireEvent.click(installBtn);
      expect(triggerInstall).toHaveBeenCalled();
    });

    it('dismisses install banner when close button is clicked', () => {
      vi.spyOn(registerSwModule, 'usePwa').mockReturnValue({
        isInstallable: true,
        isOnline: true,
        updateAvailable: false,
        triggerInstall: vi.fn(),
        applyUpdate: vi.fn(),
      });

      render(<InstallPrompt />);

      const closeBtn = screen.getByLabelText('Dismiss install prompt');
      fireEvent.click(closeBtn);

      expect(screen.queryByText('Install DSAapp')).not.toBeInTheDocument();
    });
  });

  describe('PwaUpdateToast Component', () => {
    it('does not render when update is not available', () => {
      vi.spyOn(registerSwModule, 'usePwa').mockReturnValue({
        isInstallable: false,
        isOnline: true,
        updateAvailable: false,
        triggerInstall: vi.fn(),
        applyUpdate: vi.fn(),
      });

      const { container } = render(<PwaUpdateToast />);
      expect(container.firstChild).toBeNull();
    });

    it('renders update toast when updateAvailable is true and invokes applyUpdate', () => {
      const applyUpdate = vi.fn();
      vi.spyOn(registerSwModule, 'usePwa').mockReturnValue({
        isInstallable: false,
        isOnline: true,
        updateAvailable: true,
        triggerInstall: vi.fn(),
        applyUpdate,
      });

      render(<PwaUpdateToast />);

      expect(screen.getByText('App Update Available')).toBeInTheDocument();
      expect(screen.getByText(/A new version of DSAapp has been downloaded/i)).toBeInTheDocument();

      const updateBtn = screen.getByRole('button', { name: 'Update Now' });
      fireEvent.click(updateBtn);
      expect(applyUpdate).toHaveBeenCalled();
    });
  });
});
