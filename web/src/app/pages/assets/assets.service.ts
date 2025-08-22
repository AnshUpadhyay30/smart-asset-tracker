// web/src/app/pages/assets/assets.service.ts
import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { environment } from '../../../environments/environment';
import { Observable } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class AssetService {
  private baseUrl = `${environment.apiUrl}/api/assets`;

  constructor(private http: HttpClient) {}

  // Date ko Y-M-D string me convert (datepicker Date -> API string)
  private toYmd(d: any): string | null {
    if (!d) return null;
    if (d instanceof Date && !isNaN(d.getTime())) {
      const y = d.getFullYear();
      const m = String(d.getMonth() + 1).padStart(2, '0');
      const day = String(d.getDate()).padStart(2, '0');
      return `${y}-${m}-${day}`;
    }
    return typeof d === 'string' ? d : null;
  }

  // Sirf required fields bhejo (server Marshmallow ko suit kare)
  private shape(data: any) {
    const d = data || {};
    const purchaseRaw = d.purchase_date ?? d.purchaseDate ?? null;
    const purchase = this.toYmd(purchaseRaw) ?? purchaseRaw;

    return {
      name: d.name ?? '',
      category: d.category ?? '',
      location: d.location ?? '',
      purchase_date: purchase,
      // 👇 extra kuch nahi — id/qr/created_at server handle karega
    };
  }

  getAssets(): Observable<any> {
    return this.http.get<any>(`${this.baseUrl}`);
  }

  createAsset(data: any): Observable<any> {
    return this.http.post<any>(`${this.baseUrl}`, this.shape(data));
  }

  updateAsset(id: number, data: any): Observable<any> {
    return this.http.put<any>(`${this.baseUrl}/${id}`, this.shape(data));
  }

  deleteAsset(id: number): Observable<any> {
    return this.http.delete<any>(`${this.baseUrl}/${id}`);
  }

  getAssetById(id: number): Observable<any> {
    return this.http.get<any>(`${this.baseUrl}/${id}`);
  }
}