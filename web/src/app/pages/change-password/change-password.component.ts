// 📄 src/app/pages/change-password/change-password.component.ts
import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';

import { AuthService } from '../../core/services/auth.service';

@Component({
  standalone: true,
  selector: 'app-change-password',
  imports: [CommonModule, ReactiveFormsModule, MatButtonModule, MatFormFieldModule, MatInputModule],
  template: `
  <div class="cp-wrap">
    <h2>Set New Password</h2>
    <p class="hint">Please set a strong password (min 8 characters).</p>

    <form [formGroup]="form" (ngSubmit)="submit()">
      <mat-form-field appearance="outline" class="w">
        <mat-label>New password</mat-label>
        <input matInput type="password" formControlName="new_password" required>
      </mat-form-field>

      <button mat-flat-button color="primary" [disabled]="form.invalid || saving">
        {{ saving ? 'Saving…' : 'Update Password' }}
      </button>
    </form>

    <div class="err" *ngIf="error">{{ error }}</div>
  </div>
  `,
  styles: [`
    .cp-wrap{max-width:440px;margin:6vh auto;padding:24px;border-radius:12px;background:#fff;box-shadow:0 8px 24px rgba(0,0,0,.06)}
    h2{margin:0 0 6px 0}
    .hint{margin:0 0 16px 0;color:#6b7280}
    .w{width:100%}
    .err{margin-top:10px;color:#b42318;background:#fde6e6;border:1px solid #f0b3b3;padding:8px 10px;border-radius:8px}
  `]
})
export class ChangePasswordComponent {
  private http = inject(HttpClient);
  private router = inject(Router);
  private auth = inject(AuthService);
  private fb = inject(FormBuilder);

  saving = false;
  error: string | null = null;
  form = this.fb.group({ new_password: ['', [Validators.required, Validators.minLength(8)]] });

  submit() {
    if (this.form.invalid) return;
    this.saving = true; this.error = null;

    this.auth.changePassword(this.form.value.new_password!).subscribe({
      next: () => {
        // update local storage flag
        const me = this.auth.load();
        if (me) { me.must_change_password = false; localStorage.setItem('smartasset_auth', JSON.stringify(me)); }
        this.router.navigateByUrl('/dashboard');
      },
      error: (err) => {
        this.error = err?.error?.error || 'Failed to update password';
        this.saving = false;
      }
    });
  }
}