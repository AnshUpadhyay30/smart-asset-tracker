import { Component, OnInit, signal, inject, ViewEncapsulation } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, Validators, FormsModule } from '@angular/forms';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule }  from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule }   from '@angular/material/icon';
import { MatTableModule }  from '@angular/material/table';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatSnackBar } from '@angular/material/snack-bar';
import { MatDialog } from '@angular/material/dialog';

import { AdminUsersService, AdminUser, Role } from '../../core/services/admin-users.service';
import { AuthService } from '../../core/services/auth.service';
import { ConfirmDialogComponent } from '../../components/confirm-dialog/confirm-dialog.component';

@Component({
  standalone: true,
  selector: 'app-admin-users',
  imports: [
    CommonModule, ReactiveFormsModule, FormsModule,
    MatFormFieldModule, MatInputModule, MatSelectModule,
    MatButtonModule, MatIconModule, MatTableModule,
    MatSlideToggleModule, MatTooltipModule
  ],
  templateUrl: './admin-users.component.html',
  styleUrls: ['./admin-users.component.scss'],
  encapsulation: ViewEncapsulation.None
})
export class AdminUsersComponent implements OnInit {
  // table columns (temp column included)
  cols = ['name', 'username', 'role', 'active', 'temp', 'actions'] as const;

  private fb = inject(FormBuilder);
  private api = inject(AdminUsersService);
  private auth = inject(AuthService);
  private snack = inject(MatSnackBar);
  private dlg = inject(MatDialog);

  tab = signal<'single'|'bulk'>('single');

  form = this.fb.group({
    name: ['', Validators.required],
    email: ['', [Validators.required, Validators.email]],
    role: ['MANAGER' as Role, Validators.required],
    username: [''],
    temp_password: ['']
  });

  rows = signal<AdminUser[]>([]);
  creating = signal(false);
  createdPw = signal<string | null>(null);
  formError = signal<string | null>(null);

  // session-only passwords (so action ke turant baad dikhe)
  private tempPwMap = new Map<number, string>();

  // bulk
  csv = '';
  bulkCreated = signal<any[]>([]);
  bulkErrors = signal<any[]>([]);

  ngOnInit() { this.refresh(); }

  isAdmin(): boolean { return (this.auth.role() || '') === 'ADMIN'; }

  refresh() {
    this.api.list().subscribe(u => this.rows.set(u || []));
  }

  autoSuggestUsername() {
    const name = this.form.value.name || '';
    const email = this.form.value.email || '';
    if (!name && !email) return;
    if ((this.form.value.username || '').trim()) return;
    this.api.suggestUsername(name, email).subscribe(r => {
      if (r?.username) this.form.patchValue({ username: r.username });
    });
  }

  // ✅ table me dikhane ke लिए: session map → fallback to server value
  tempPwFor(userId: number): string | null {
    const inSession = this.tempPwMap.get(userId);
    if (inSession) return inSession;
    const row = (this.rows() || []).find(r => r.id === userId);
    return row?.last_temp_password || null;
    // ↑ refresh के बाद भी value रहेगी (server से आती है)
  }

  // ---- Create
  createSingle() {
    if (this.form.invalid || !this.isAdmin()) return;
    this.creating.set(true);
    this.formError.set(null);
    this.createdPw.set(null);

    const raw = this.form.value as any;
    const payload: any = { name: raw.name, email: raw.email, role: raw.role };
    if (raw.username && raw.username.trim()) payload.username = raw.username.trim();
    if (raw.temp_password && raw.temp_password.trim()) payload.temp_password = raw.temp_password.trim();

    this.api.create(payload).subscribe({
      next: (res: any) => {
        if (res?.id && res?.temp_password) {
          this.tempPwMap.set(res.id, res.temp_password);
          this.createdPw.set(res.temp_password);
        }
        this.snack.open('User created', '', { duration: 1800 });
        this.form.reset({ role: 'MANAGER' });
        this.refresh();
      },
      error: (err) => {
        this.snack.open(this.readError(err) || 'Create failed', 'Dismiss', { duration: 3000 });
      },
      complete: () => this.creating.set(false)
    });
  }

  // ---- Bulk CSV
  bulkCreateCsv() {
    if (!this.isAdmin()) return;
    this.bulkCreated.set([]); this.bulkErrors.set([]);
    const csv = (this.csv || '').trim(); if (!csv) return;

    this.api.bulkCreateCsv(csv).subscribe({
      next: ({created, errors}) => {
        (created || []).forEach((c: any) => {
          if (c?.id && c?.temp_password) this.tempPwMap.set(c.id, c.temp_password);
        });
        this.bulkCreated.set(created || []);
        this.bulkErrors.set(errors || []);
        this.snack.open('Bulk create complete', '', { duration: 1800 });
        this.refresh();
      },
      error: (e) => this.snack.open(this.readError(e) || 'Bulk create failed', 'Dismiss', { duration: 3000 })
    });
  }

  downloadCsvTemplate() {
    const tpl = "name,email,role,username\nRohit,rohit@example.com,MANAGER,rohit.ch\nPriya,priya@example.com,TECH,\n";
    const blob = new Blob([tpl], {type:"text/csv;charset=utf-8"});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a'); a.href = url; a.download = 'users_template.csv'; a.click();
    URL.revokeObjectURL(url);
  }

  // ---- Export CSV (server + session temp passwords)
  exportCsv() {
    const items = this.rows() || [];
    const headers = ['name','email','username','role','is_active','temp_password'];
    const lines = [headers.join(',')];
    items.forEach(u => {
      const temp = this.tempPwFor(u.id) || '';
      const row = [safe(u.name), safe(u.email), safe(u.username || ''), safe(u.role), u.is_active ? 'true' : 'false', safe(temp)];
      lines.push(row.join(','));
    });
    const blob = new Blob([lines.join('\n')], { type: 'text/csv;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a'); a.href = url; a.download = `users_${today()}.csv`; a.click();
    URL.revokeObjectURL(url);

    function safe(v: string) { const s = String(v ?? ''); return /[",\n]/.test(s) ? `"${s.replace(/"/g,'""')}"` : s; }
    function today() { return new Date().toISOString().slice(0,10); }
  }

  // ---- Inline table actions
  changeRole(u: AdminUser, role: Role) {
    if (!this.isAdmin()) return;
    this.api.updateRole(u.id, role).subscribe({
      next: () => this.refresh(),
      error: e => this.snack.open(this.readError(e) || 'Role update failed', 'Dismiss', { duration: 3000 })
    });
  }

  toggleActive(u: AdminUser, is_active: boolean) {
    if (!this.isAdmin()) return;
    const ref = this.dlg.open(ConfirmDialogComponent, {
      width: '420px',
      data: {
        title: is_active ? 'Enable User' : 'Disable User',
        message: is_active ? `Allow ${u.name} to sign in?`
                           : `Disable ${u.name}? They will not be able to sign in until re-enabled.`,
        okText: is_active ? 'Enable' : 'Disable',
        cancelText: 'Cancel'
      }
    });
    ref.afterClosed().subscribe(ok => {
      if (!ok) return;
      this.api.toggleActive(u.id, is_active).subscribe({
        next: () => { this.snack.open(is_active ? 'User enabled' : 'User disabled', '', { duration: 1500 }); this.refresh(); },
        error: e => this.snack.open(this.readError(e) || 'Status change failed', 'Dismiss', { duration: 3000 })
      });
    });
  }

  // ---- Reset Password (persist + UI)
  resetPassword(u: AdminUser) {
    if (!this.isAdmin()) return;
    const ref = this.dlg.open(ConfirmDialogComponent, {
      width: '420px',
      data: { title: 'Reset Password', message: `Issue a new temporary password for ${u.name}?`, okText: 'Reset', cancelText: 'Cancel' }
    });
    ref.afterClosed().subscribe(ok => {
      if (!ok) return;
      this.api.resetPassword(u.id).subscribe({
        next: (res: any) => {
          if (res?.temp_password) this.tempPwMap.set(u.id, res.temp_password);
          this.snack.open('Temporary password generated', '', { duration: 1800 });
          this.refresh();
        },
        error: e => this.snack.open(this.readError(e) || 'Reset failed', 'Dismiss', { duration: 3000 })
      });
    });
  }

  // ---- error helper
  private readError(err: any): string | null {
    const e = err?.error ?? err;
    if (typeof e === 'string') return e;
    if (e?.message) return e.message;
    if (e?.error?.message) return e.error.message;
    const bag = e?.errors;
    if (bag && typeof bag === 'object') {
      const k = Object.keys(bag)[0];
      const v = Array.isArray(bag[k]) ? bag[k][0] : bag[k];
      if (v) return `${k}: ${String(v)}`;
    }
    if (e?.error) return String(e.error);
    if (err?.status === 400) return 'Validation failed (400).';
    return null;
  }
}