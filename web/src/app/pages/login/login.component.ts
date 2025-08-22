// 📄 src/app/pages/login/login.component.ts
import { Component, signal } from '@angular/core';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { CommonModule } from '@angular/common';

// Angular Material
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';

import { AuthService } from '../../core/services/auth.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    MatFormFieldModule, MatInputModule,
    MatButtonModule, MatCheckboxModule,
    MatIconModule, MatProgressSpinnerModule
  ],
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.scss'],
})
export class LoginComponent {
  showPassword = signal(false);
  loading      = signal(false);
  errorMessage = signal<string>('');

  loginForm: FormGroup;

  constructor(
    private fb: FormBuilder,
    private auth: AuthService,
    private router: Router
  ) {
    this.loginForm = this.fb.group({
      email: ['', [Validators.required, Validators.email]],
      password: ['', Validators.required],
      remember: [false],
    });
  }

  onSubmit(): void {
    if (this.loginForm.invalid || this.loading()) return;
    this.errorMessage.set('');
    this.loading.set(true);

    this.auth.login(this.loginForm.value).subscribe({
      // ⬇️ Always send user to dashboard after a successful login
      next: () => {
        this.router.navigate(['/dashboard']);
      },
      error: (err: any) => {
        console.error('Login error:', err);
        const msg =
          err?.error?.error || err?.error?.message ||
          'Login failed. Please check your credentials.';
        this.errorMessage.set(msg);
        this.loading.set(false);
      },
      complete: () => this.loading.set(false),
    });
  }
}