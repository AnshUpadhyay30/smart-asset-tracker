import { Component, ViewChild, inject } from '@angular/core';
import { CommonModule } from '@angular/common';

import { MatTableModule, MatTableDataSource } from '@angular/material/table';
import { MatSort, MatSortModule } from '@angular/material/sort';
import { MatPaginator, MatPaginatorModule } from '@angular/material/paginator';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatDividerModule } from '@angular/material/divider';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';

import { AssetService } from './assets.service';
import { AssetDialogComponent } from '../../components/asset-dialog.component';
import { environment } from '../../../environments/environment';
import { AuthService } from '../../core/services/auth.service';

// ✅ NEW: import the confirm dialog symbol
import { ConfirmDialogComponent } from '../../components/confirm-dialog/confirm-dialog.component';

export interface AssetRow {
  id: number;
  name?: string;
  category?: string;
  location?: string;
  purchase_date?: string | null;
  qr_code_path?: string;
}

@Component({
  standalone: true,
  selector: 'app-assets',
  templateUrl: './assets.component.html',
  styleUrls: ['./assets.component.scss'],
  imports: [
    CommonModule,
    MatTableModule, MatSortModule, MatPaginatorModule,
    MatIconModule, MatButtonModule, MatFormFieldModule, MatInputModule,
    MatSelectModule, MatTooltipModule, MatDividerModule, MatProgressBarModule,
    MatDialogModule, MatSnackBarModule
  ]
})
export class AssetsComponent {
  private readonly apiOrigin = environment.apiUrl || '';
  private readonly svc = inject(AssetService);
  private readonly dlg = inject(MatDialog);
  private readonly auth = inject(AuthService);
  private readonly snack = inject(MatSnackBar);

  dataSource = new MatTableDataSource<AssetRow>([]);
  displayedColumns: string[] = ['name', 'category', 'location', 'purchase_date', 'actions'];

  @ViewChild(MatSort, { static: true }) sort!: MatSort;
  @ViewChild(MatPaginator, { static: true }) paginator!: MatPaginator;

  loading = false;
  categories: string[] = [];
  locations: string[] = [];
  selectedCategory = '';
  selectedLocation = '';

  ngOnInit(): void { this.fetchAssets(); }

  // ---- RBAC helpers
  isAdmin(): boolean { return this.auth.role() === 'ADMIN'; }
  isManagerOrAdmin(): boolean {
    const r = this.auth.role() || '';
    return r === 'ADMIN' || r === 'MANAGER';
  }

  // ---- Server error → readable message
  private readServerError(err: any): string {
    const e = err?.error ?? err;
    if (typeof e === 'string') return e;
    if (e?.message) return e.message;
    if (e?.error?.message) return e.error.message;
    const bag = e?.errors;
    if (bag && typeof bag === 'object') {
      const firstKey = Object.keys(bag)[0];
      const val = Array.isArray(bag[firstKey]) ? bag[firstKey][0] : bag[firstKey];
      if (val) return `${firstKey}: ${String(val)}`;
    }
    if (err?.status === 400) return 'Validation failed (400). Please check fields.';
    if (err?.status === 500) return 'Server error (500). Please try again.';
    return 'Request failed';
  }

  // ---- Load table
  fetchAssets(): void {
    this.loading = true;
    this.svc.getAssets().subscribe({
      next: (res: any) => {
        const items: AssetRow[] = Array.isArray(res?.items) ? res.items : (Array.isArray(res) ? res : []);
        this.dataSource.data = items;
        this.dataSource.sort = this.sort;
        this.dataSource.paginator = this.paginator;

        this.categories = Array.from(new Set(items.map(x => String(x.category ?? '')).filter(Boolean))).sort();
        this.locations  = Array.from(new Set(items.map(x => String(x.location ?? '')).filter(Boolean))).sort();

        // text + dropdown filter
        this.dataSource.filterPredicate = (row: AssetRow, raw: string) => {
          const f = JSON.parse(raw) as { text: string; category: string; location: string };
          const text = (f.text || '').toLowerCase();
          const textHit =
            (row.name ?? '').toLowerCase().includes(text) ||
            (row.category ?? '').toLowerCase().includes(text) ||
            (row.location ?? '').toLowerCase().includes(text) ||
            (row.purchase_date ?? '').toLowerCase().includes(text);
          const catHit = !f.category || row.category === f.category;
          const locHit = !f.location || row.location === f.location;
          return textHit && catHit && locHit;
        };
      },
      error: (err) => this.snack.open(this.readServerError(err) || 'Failed to load assets', 'Dismiss', { duration: 3500 }),
      complete: () => (this.loading = false)
    });
  }

  // ---- Filters
  applyQuickFilter(value: string): void {
    this.dataSource.filter = JSON.stringify({
      text: (value || '').trim().toLowerCase(),
      category: this.selectedCategory,
      location: this.selectedLocation
    });
    this.dataSource.paginator?.firstPage();
  }
  onFilterChange(): void {
    const el = document.getElementById('asset-search') as HTMLInputElement | null;
    this.applyQuickFilter(el?.value ?? '');
  }
  clearFilters(): void {
    this.selectedCategory = '';
    this.selectedLocation = '';
    this.applyQuickFilter('');
  }

  // ---- Add / Edit
  openAddAssetDialog(): void {
    const ref = this.dlg.open(AssetDialogComponent, { width: '520px' });
    ref.afterClosed().subscribe(payload => {
      if (!payload) return;
      this.loading = true;
      this.svc.createAsset(payload).subscribe({
        next: () => { this.snack.open('Asset created', '', { duration: 2000 }); this.fetchAssets(); },
        error: (err) => { this.snack.open(this.readServerError(err), 'Dismiss', { duration: 4000 }); this.loading = false; }
      });
    });
  }

  editAsset(asset: AssetRow): void {
    const ref = this.dlg.open(AssetDialogComponent, { width: '520px', data: asset });
    ref.afterClosed().subscribe(payload => {
      if (!payload) return;
      const id = asset?.id ?? payload?.id;
      if (!id) { this.snack.open('Missing asset id', 'Dismiss', { duration: 2500 }); return; }
      this.loading = true;
      this.svc.updateAsset(id, payload).subscribe({
        next: () => { this.snack.open('Changes saved', '', { duration: 2000 }); this.fetchAssets(); },
        error: (err) => { this.snack.open(this.readServerError(err), 'Dismiss', { duration: 4000 }); this.loading = false; }
      });
    });
  }

  // ---- Delete (with professional confirm dialog)
  deleteAsset(id: number): void {
    if (!id) {
      this.snack.open('Invalid asset id', 'Dismiss', { duration: 2500 });
      return;
    }

    const ref = this.dlg.open(ConfirmDialogComponent, {
      width: '420px',
      data: {
        title: 'Delete Asset',
        message: 'Do you really want to delete this asset? This action cannot be undone.'
      }
    });

    ref.afterClosed().subscribe(result => {
      if (!result) return; // user pressed Cancel

      this.loading = true;
      this.svc.deleteAsset(id).subscribe({
        next: () => {
          this.snack.open('Asset deleted successfully', '', { duration: 2000 });
          this.fetchAssets();
        },
        error: (err) => {
          const msg = (err?.status === 500)
            ? 'Cannot delete: asset has maintenance logs. (Ask admin to remove logs or enable cascade)'
            : this.readServerError(err);
          this.snack.open(msg, 'Dismiss', { duration: 5000 });
          this.loading = false;
        }
      });
    });
  }

  // ---- Helpers
  exportCSV(): void {
    const rows = this.dataSource.filteredData.length ? this.dataSource.filteredData : this.dataSource.data;
    const csv = [
      ['Name', 'Category', 'Location', 'Purchase Date'].join(','),
      ...rows.map(r =>
        [r.name, r.category, r.location, this.formatDate(r.purchase_date)]
          .map(v => `"${(v ?? '').toString().replace(/"/g, '""')}"`)
          .join(',')
      )
    ].join('\n');

    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `assets_${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }

  trackById(_i: number, row: AssetRow): number { return row.id; }

  hasQr(row: AssetRow): boolean { return !!String((row.qr_code_path ?? '')).trim(); }

  qrHref(row: AssetRow): string {
    const raw = String((row as any)?.qr_code_path || '').trim();
    if (/^https?:\/\//i.test(raw)) return raw;
    const file = raw.split('/').pop() || raw;
    return `${this.apiOrigin}/api/qr/${file}`;
  }

  formatDate(d: string | null | undefined): string {
    if (!d) return '';
    const s = d.length >= 10 ? d.slice(0, 10) : d; // 'YYYY-MM-DDTHH:mm' → 'YYYY-MM-DD'
    const dt = new Date(s);
    if (isNaN(dt.getTime())) return s;
    const y = dt.getFullYear();
    const m = String(dt.getMonth() + 1).padStart(2, '0');
    const day = String(dt.getDate()).padStart(2, '0');
    return `${y}-${m}-${day}`;
  }
}