// src/app/core/services/admin-users.service.ts
import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { environment } from '../../../environments/environment';
import { Observable } from 'rxjs';

export type Role = 'ADMIN' | 'MANAGER' | 'TECH';

export interface AdminUser {
  id: number;
  name: string;
  email: string;
  username?: string | null;
  role: Role;
  is_active: boolean;
  must_change_password: boolean;
  // ✅ server se aayega; refresh par table me dikhane ke liye
  last_temp_password?: string | null;
}

@Injectable({ providedIn: 'root' })
export class AdminUsersService {
  private base = `${environment.apiUrl}/api/admin/users`;

  constructor(private http: HttpClient) {}

  list(): Observable<AdminUser[]> {
    return this.http.get<AdminUser[]>(this.base);
  }

  // returns id + temp_password on success
  create(payload: { name: string; email: string; role: Role; username?: string; temp_password?: string }) {
    return this.http.post<{ id: number; temp_password: string; username: string }>(this.base, payload);
  }

  bulkCreate(users: Array<{ name: string; email: string; role: Role; username?: string }>) {
    return this.http.post<{ created: any[]; errors: any[] }>(`${this.base}/bulk`, { users });
  }

  // CSV-based bulk
  bulkCreateCsv(csv: string) {
    return this.http.post<{ created: any[]; errors: any[] }>(`${this.base}/bulk`, { csv });
  }

  suggestUsername(name?: string, email?: string) {
    let params = new HttpParams();
    if (name) params = params.set('name', name);
    if (email) params = params.set('email', email);
    return this.http.get<{ username: string }>(`${this.base}/suggest-username`, { params });
  }

  updateRole(userId: number, role: Role) {
    return this.http.put<{ message: string }>(`${this.base}/${userId}/role`, { role });
  }

  toggleActive(userId: number, is_active: boolean) {
    return this.http.put<{ message: string; is_active: boolean }>(`${this.base}/${userId}/status`, { is_active });
  }

  // backend returns temp_password; UI table shows it
  resetPassword(userId: number, temp_password?: string) {
    return this.http.post<{ message: string; temp_password?: string; user_id?: number }>(
      `${this.base}/${userId}/reset-password`,
      { temp_password }
    );
  }
}