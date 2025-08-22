// src/app/pages/reports/reports.service.ts
import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { environment } from '../../../environments/environment';
import { Observable } from 'rxjs';

export interface MonthlyCost {
  year: number;
  month: number; // 1..12
  total_cost: number;
}

export interface ExpiringAsset {
  id: number;
  name: string;
  category: string;
  warranty_end: string; // YYYY-MM-DD
}

@Injectable({ providedIn: 'root' })
export class ReportsService {
  private base = `${environment.apiUrl}`;

  constructor(private http: HttpClient) {}

  getMonthlyCost(): Observable<MonthlyCost[]> {
    return this.http.get<MonthlyCost[]>(`${this.base}/api/reports/monthly-cost`);
  }

  getWarrantyExpiring(days = 30): Observable<ExpiringAsset[]> {
    const params = new HttpParams().set('days', String(days));
    return this.http.get<ExpiringAsset[]>(`${this.base}/api/reports/warranty-expiring`, { params });
  }

  downloadAssetsCsv() {
    return this.http.get(`${this.base}/api/reports/assets/export`, { responseType: 'blob' });
  }

  downloadLogsCsv() {
    return this.http.get(`${this.base}/api/reports/logs/export`, { responseType: 'blob' });
  }
}