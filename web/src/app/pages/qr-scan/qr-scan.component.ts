import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';

import { ZXingScannerModule } from '@zxing/ngx-scanner';
import { BarcodeFormat } from '@zxing/library';
import { BrowserMultiFormatReader } from '@zxing/browser';

import { MatFormFieldModule } from '@angular/material/form-field';
import { MatSelectModule } from '@angular/material/select';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatCardModule } from '@angular/material/card';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatTooltipModule } from '@angular/material/tooltip';
import { FormsModule } from '@angular/forms';

import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environments/environment';

@Component({
  standalone: true,
  selector: 'app-qr-scan',
  templateUrl: './qr-scan.component.html',
  styleUrls: ['./qr-scan.component.scss'],
  imports: [
    CommonModule, FormsModule,
    ZXingScannerModule,
    MatFormFieldModule, MatSelectModule,
    MatButtonModule, MatIconModule, MatCardModule,
    MatProgressBarModule, MatTooltipModule
  ],
})
export class QrScanComponent {
  private http = inject(HttpClient);

  // API base (unchanged for fetch)
  private apiBase = `${environment.apiUrl}/api`;
  // Base for building image URLs
  private apiUrl = environment.apiUrl || '';

  // camera devices
  devices: MediaDeviceInfo[] = [];
  currentDevice: MediaDeviceInfo | null = null;

  // states
  hasPermission = signal<boolean | null>(null);
  torchAvailable = signal(false);
  torchOn = signal(false);
  formats = [BarcodeFormat.QR_CODE];
  scanning = signal(true);

  // results
  lastText = signal<string | null>(null);
  loadingAsset = signal(false);
  asset: any | null = null;
  error = signal<string | null>(null);

  // permissions
  onScanPermission(p: boolean) { this.hasPermission.set(p); }

  onCamerasFound(devs: MediaDeviceInfo[]) {
    this.devices = devs;
    const back = devs.find(d => /back|rear|environment/i.test(d.label));
    this.currentDevice = back || devs[0] || null;
  }

  onTorchCompatible(is: boolean) { this.torchAvailable.set(is); }
  toggleTorch() { this.torchOn.set(!this.torchOn()); }

  // scan success
  onCodeResult(text: string) {
    if (!text || text === this.lastText()) return;
    this.lastText.set(text);
    this.fetchAssetFromPayload(text);
  }

  // Build a public URL for the QR image (no API change)
  qrUrl(raw: string): string {
    if (!raw) return '';
    const val = String(raw).trim();
    if (/^https?:\/\//i.test(val)) return val;             // already absolute
    const file = val.split('/').pop() || val;              // keep just the filename
    return `${this.apiUrl}/api/uploads/${file}`;           // same pattern as backend _upload_url
  }

  // If /api/uploads/* 404s, try /api/qr/* once as a fallback (TS4111-safe)
  onQrImgError(ev: Event) {
    const img = ev.target as HTMLImageElement;
    const ds = img.dataset as DOMStringMap;

    if (ds['fallback'] === 'done') return;                // avoid loop
    ds['fallback'] = 'done';

    const file = (img.src.split('/').pop() || '').split('?')[0];
    img.src = `${this.apiUrl}/api/qr/${file}`;
  }

  // Parse common QR payloads then fetch
  private fetchAssetFromPayload(text: string) {
    this.error.set(null);
    this.asset = null;

    let id: number | null = null;

    const num = text.match(/^\d+$/)?.[0];
    if (num) id = +num;

    if (!id) {
      const pref = text.match(/ASSET:(\d+)/i);
      if (pref) id = +pref[1];
    }

    if (!id) {
      const url = text.match(/assets\/(\d+)(?!.*assets\/\d+)/i);
      if (url) id = +url[1];
    }

    if (!id || isNaN(id)) {
      this.error.set('QR does not contain a valid Asset ID.');
      return;
    }

    this.loadingAsset.set(true);
    this.http.get(`${this.apiBase}/assets/${id}`).subscribe({
      next: (data) => { this.asset = data; },
      error: () => { this.error.set('Asset not found or API error.'); },
      complete: () => this.loadingAsset.set(false)
    });
  }

  // Decode from uploaded image
  async onFile(e: Event) {
    const file = (e.target as HTMLInputElement).files?.[0];
    if (!file) return;
    const url = URL.createObjectURL(file);
    try {
      const reader = new BrowserMultiFormatReader();
      const res = await reader.decodeFromImageUrl(url);
      this.onCodeResult(res.getText());
    } catch {
      this.error.set('Could not read QR from image.');
    } finally {
      URL.revokeObjectURL(url);
    }
  }

  clear() {
    this.lastText.set(null);
    this.asset = null;
    this.error.set(null);
  }
}