// 📄 src/app/core/services/auth.service.ts
import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Router } from '@angular/router';
import { Observable, tap } from 'rxjs';

export interface Me {
  access_token: string;
  role: 'ADMIN' | 'MANAGER' | 'TECH';
  must_change_password: boolean;
  is_active: boolean;
  name: string;
  email: string;
}

@Injectable({ providedIn: 'root' })
export class AuthService {
  private apiUrl = 'http://localhost:5000/api/auth';
  private KEY = 'smartasset_auth';

  constructor(private http: HttpClient, private router: Router) {}

  /** 🔐 Login: stores the whole user payload (token + meta) */
  login(credentials: { email: string; password: string }): Observable<Me> {
    const headers = new HttpHeaders({ 'Content-Type': 'application/json' });

    return this.http.post<Me>(`${this.apiUrl}/login`, credentials, {
      headers,
      withCredentials: false
    }).pipe(
      tap(res => {
        localStorage.setItem(this.KEY, JSON.stringify(res));
      })
    );
  }

  /** ↪️ Change password (first login flow) */
  changePassword(new_password: string): Observable<{ message: string }> {
    const headers = new HttpHeaders({ 'Content-Type': 'application/json' });
    return this.http.post<{ message: string }>(
      `${this.apiUrl}/change-password`,
      { new_password },
      { headers }
    );
  }

  /** 📥 Load currently stored auth payload */
  load(): Me | null {
    const raw = localStorage.getItem(this.KEY);
    return raw ? (JSON.parse(raw) as Me) : null;
  }

  /** 🎫 JWT token getter */
  getToken(): string | null {
    return this.load()?.access_token ?? null;
  }

  /** 👤 role getter */
  role(): Me['role'] | null {
    return this.load()?.role ?? null;
  }

  /** 🔁 must-change-password flag */
  mustChangePassword(): boolean {
    return !!this.load()?.must_change_password;
  }

  /** ✅ active login? */
  isLoggedIn(): boolean {
    return !!this.getToken();
  }

  /** 🚪 Logout */
  logout(): void {
    localStorage.removeItem(this.KEY);
    this.router.navigate(['/login']);
  }

  /** (Optional) Dummy Google Sign-In hook */
  googleSignIn(): Promise<any> {
    return Promise.reject({ message: 'Google Sign-In not implemented' });
  }
}