// 📄 src/app/layout/main-layout.component.ts
import { Component, inject } from '@angular/core';
import { Router, RouterModule } from '@angular/router';
import { CommonModule } from '@angular/common';
import { AuthService } from '../core/services/auth.service';

@Component({
  selector: 'app-main-layout',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: 'main-layout.component.html',
  styleUrls: ['main-layout.component.scss'],
})
export class MainLayoutComponent {
  private auth = inject(AuthService);
  private router = inject(Router);

  // ── Role helpers ──────────────────────────────────────────
  isAdmin(): boolean { return this.auth.role() === 'ADMIN'; }
  isManagerOrAdmin(): boolean {
    const r = this.auth.role();
    return r === 'ADMIN' || r === 'MANAGER';
  }
  role(): 'ADMIN' | 'MANAGER' | 'TECH' | null { return this.auth.role(); }
  userName(): string { return this.auth.load()?.name ?? ''; }

  /** Avatar initials (e.g., "Ansh Upadhyay" → "AU") */
  initials(): string {
    const n = (this.userName() || '').trim();
    if (!n) return 'U';
    const parts = n.split(/\s+/);
    const first = parts[0]?.[0] ?? '';
    const second = parts[1]?.[0] ?? '';
    return (first + (second || '') || first).toUpperCase();
  }

  // ── Logout ────────────────────────────────────────────────
  logout(): void {
    this.auth.logout();
    this.router.navigate(['/login']);
  }
}