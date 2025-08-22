// 📄 src/app/app.routes.ts
import { Routes } from '@angular/router';
import { provideRouter } from '@angular/router';

import { LoginComponent } from './pages/login/login.component';
import { DashboardComponent } from './pages/dashboard/dashboard.component';
import { AssetsComponent } from './pages/assets/assets.component';
import { MaintenanceComponent } from './pages/maintenance/maintenance.component';
import { ReportsComponent } from './pages/reports/reports.component';
import { QrScanComponent } from './pages/qr-scan/qr-scan.component';
import { ChangePasswordComponent } from './pages/change-password/change-password.component';

import { authGuard } from './core/guards/auth.guard';
import { MainLayoutComponent } from './layout/main-layout.component';
import { IsAdminGuard } from './core/guards/is-admin.guard'; // ✅ Admin-only guard

export const routes: Routes = [
  // 🏁 Default → login
  { path: '', redirectTo: 'login', pathMatch: 'full' },

  // 🔓 Public
  { path: 'login', component: LoginComponent },

  // 🔐 Protected shell + child pages
  {
    path: '',
    component: MainLayoutComponent,
    canActivate: [authGuard],
    children: [
      { path: 'dashboard', component: DashboardComponent },
      { path: 'assets', component: AssetsComponent },
      { path: 'maintenance', component: MaintenanceComponent },
      { path: 'reports', component: ReportsComponent },
      { path: 'qr-scan', component: QrScanComponent },

      // 🔒 First-login flow (requires token; kept inside protected shell)
      { path: 'change-password', component: ChangePasswordComponent },

      // 👮‍♂️ Admin-only Users page (lazy load)
      {
        path: 'users',
        canActivate: [IsAdminGuard],
        loadComponent: () =>
          import('./pages/admin-users/admin-users.component')
            .then(m => m.AdminUsersComponent)
      },
    ],
  },

  // ❌ Fallback
  { path: '**', redirectTo: 'login' },
];

// Provide router from this module
export const appRouter = provideRouter(routes);