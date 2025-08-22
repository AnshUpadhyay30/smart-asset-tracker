// 📁 src/app/core/services/reports.service.ts
import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

// ✅ Matches Flask response keys
export interface DashboardSummary {
  total_assets: number;
  total_logs: number;
  overdue_logs: number;
  monthly_cost: {
    month: string;
    cost: number;
  }[];
}

@Injectable({
  providedIn: 'root'
})
export class ReportsService {
  private baseUrl = environment.apiUrl;  // ✅ e.g. http://localhost:5000

  constructor(private http: HttpClient) {}

  // ✅ GET: /api/assets/dashboard-summary
  getDashboardSummary(): Observable<DashboardSummary> {
    return this.http.get<DashboardSummary>(`${this.baseUrl}/api/assets/dashboard-summary`);
  }
}