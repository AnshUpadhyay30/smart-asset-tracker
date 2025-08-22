import { Injectable, inject } from '@angular/core';
import { CanActivate, Router } from '@angular/router';
import { AuthService } from '../services/auth.service';

@Injectable({ providedIn: 'root' })
export class IsAdminGuard implements CanActivate {
  private auth = inject(AuthService);
  private router = inject(Router);

  canActivate(): boolean {
    const role = this.auth.role();
    if (role === 'ADMIN') return true;
    this.router.navigate(['/dashboard']);
    return false;
  }
}