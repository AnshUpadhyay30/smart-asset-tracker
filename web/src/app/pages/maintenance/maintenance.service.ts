import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { environment } from '../../../environments/environment';
import { Observable } from 'rxjs';

export interface Asset {
  id: number;
  name: string;
  category?: string;
  location?: string;
}

export interface MaintenanceLog {
  id: number;
  asset_id: number;
  service_date: string;     // 'YYYY-MM-DD'
  description?: string;
  parts_used?: string;
  cost?: number;
  technician_id?: number;
  next_service_due?: string | null;
  attachment_path?: string | null;
}

@Injectable({ providedIn: 'root' })
export class MaintenanceService {
  private http = inject(HttpClient);
  private base = environment.apiUrl;

  // Assets (for select dropdown)
  getAssets(): Observable<{ items: Asset[] } | Asset[]> {
    return this.http.get<{ items: Asset[] } | Asset[]>(`${this.base}/api/assets`);
  }

  // Logs for one asset
  getLogs(assetId: number): Observable<MaintenanceLog[]> {
    return this.http.get<MaintenanceLog[]>(`${this.base}/api/assets/${assetId}/maintenance`);
  }

  // Create log (TECH)
  createLog(assetId: number, payload: Partial<MaintenanceLog>) {
    return this.http.post(`${this.base}/api/assets/${assetId}/maintenance`, payload);
  }

  // Update log (MANAGER)
  updateLog(logId: number, payload: Partial<MaintenanceLog>) {
    return this.http.put(`${this.base}/api/maintenance/${logId}`, payload);
  }

  // Delete log (ADMIN)
  deleteLog(logId: number) {
    return this.http.delete(`${this.base}/api/maintenance/${logId}`);
  }
}