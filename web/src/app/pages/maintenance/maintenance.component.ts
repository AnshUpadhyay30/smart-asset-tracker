import { Component, ViewChild, inject } from '@angular/core';
import { CommonModule } from '@angular/common';

import { MatTableModule, MatTableDataSource } from '@angular/material/table';
import { MatPaginator, MatPaginatorModule } from '@angular/material/paginator';
import { MatSort, MatSortModule } from '@angular/material/sort';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatSelectModule } from '@angular/material/select';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatDividerModule } from '@angular/material/divider';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';

import { MaintenanceService, MaintenanceLog, Asset } from './maintenance.service';
import { LogDialogComponent } from '../../components/maintenance-log-dialog/log-dialog.component';
import { ConfirmDialogComponent } from '../../components/confirm-dialog/confirm-dialog.component';
import { AuthService } from '../../core/services/auth.service';

@Component({
  standalone: true,
  selector: 'app-maintenance',
  templateUrl: './maintenance.component.html',
  styleUrls: ['./maintenance.component.scss'],
  imports: [
    CommonModule,
    MatTableModule, MatPaginatorModule, MatSortModule,
    MatFormFieldModule, MatSelectModule, MatInputModule,
    MatButtonModule, MatIconModule, MatTooltipModule,
    MatDividerModule, MatProgressBarModule, MatDialogModule, MatSnackBarModule,
  ]
})
export class MaintenanceComponent {
  private api = inject(MaintenanceService);
  private dialog = inject(MatDialog);
  private snack = inject(MatSnackBar);
  private auth = inject(AuthService);

  assets: Asset[] = [];
  selectedAssetId: number | null = null;

  dataSource = new MatTableDataSource<MaintenanceLog>([]);
  displayed = ['service_date', 'description', 'parts_used', 'cost', 'next_service_due', 'actions'];

  loading = false;
  searchText = '';

  @ViewChild(MatPaginator, { static: true }) paginator!: MatPaginator;
  @ViewChild(MatSort, { static: true }) sort!: MatSort;

  ngOnInit() {
    // Load assets for dropdown
    this.api.getAssets().subscribe({
      next: (res: any) => {
        this.assets = Array.isArray(res?.items) ? res.items : (Array.isArray(res) ? res : []);
        if (this.assets?.length) {
          this.selectedAssetId = this.assets[0].id;
          this.loadLogs();
        }
      },
      error: () => this.snack.open('Failed to load assets', 'Dismiss', { duration: 3000 })
    });

    // table config
    this.dataSource.paginator = this.paginator;
    this.dataSource.sort = this.sort;
    this.dataSource.filterPredicate = (row, raw) => {
      const t = (raw || '').trim().toLowerCase();
      return (
        (row.description ?? '').toLowerCase().includes(t) ||
        (row.parts_used ?? '').toLowerCase().includes(t) ||
        (row.service_date ?? '').toLowerCase().includes(t) ||
        (row.next_service_due ?? '').toLowerCase().includes(t)
      );
    };
  }

  // ---- RBAC helpers (frontend visibility only)
  isAdmin(): boolean { return this.auth.role() === 'ADMIN'; }
  isManagerOrAdmin(): boolean { const r = this.auth.role() || ''; return r === 'ADMIN' || r === 'MANAGER'; }
  canEdit(): boolean { return this.isManagerOrAdmin(); }
  canCreate(): boolean { return this.auth.role() !== null; } // Tech/Manager/Admin can open Add (server enforces rules)

  // ---- Data ops
  loadLogs() {
    if (!this.selectedAssetId) { this.dataSource.data = []; return; }
    this.loading = true;
    this.api.getLogs(this.selectedAssetId).subscribe({
      next: logs => this.dataSource.data = logs ?? [],
      error: () => this.snack.open('Failed to load logs', 'Dismiss', { duration: 3000 }),
      complete: () => this.loading = false
    });
  }

  // ---- Search
  applySearch(value: string) {
    this.searchText = value;
    this.dataSource.filter = value || '';
    this.dataSource.paginator?.firstPage();
  }
  clearSearch() { this.applySearch(''); }

  // ---- Add
  openAddLog() {
    if (!this.selectedAssetId) return;
    const dlg = this.dialog.open(LogDialogComponent, { width: '560px', data: { mode: 'create', assetId: this.selectedAssetId } });
    dlg.afterClosed().subscribe(body => {
      if (!body) return;
      this.loading = true;
      this.api.createLog(this.selectedAssetId!, body).subscribe({
        next: () => { this.snack.open('Log added', '', { duration: 2000 }); this.loadLogs(); },
        error: (err) => { this.loading = false; this.snack.open(this.readError(err) || 'Create failed', 'Dismiss', { duration: 3500 }); }
      });
    });
  }

  // ---- Edit
  editLog(row: MaintenanceLog) {
    const dlg = this.dialog.open(LogDialogComponent, { width: '560px', data: { mode: 'edit', log: row } });
    dlg.afterClosed().subscribe(body => {
      if (!body) return;
      this.loading = true;
      this.api.updateLog(row.id, body).subscribe({
        next: () => { this.snack.open('Changes saved', '', { duration: 2000 }); this.loadLogs(); },
        error: (err) => { this.loading = false; this.snack.open(this.readError(err) || 'Update failed', 'Dismiss', { duration: 3500 }); }
      });
    });
  }

  // ---- Delete with professional confirm
  deleteLog(row: MaintenanceLog) {
    const ref = this.dialog.open(ConfirmDialogComponent, {
      width: '420px',
      data: {
        title: 'Delete Log',
        message: 'Do you really want to delete this maintenance log? This action cannot be undone.',
        okText: 'Delete',
        cancelText: 'Cancel'
      }
    });

    ref.afterClosed().subscribe(confirm => {
      if (!confirm) return;
      this.loading = true;
      this.api.deleteLog(row.id).subscribe({
        next: () => { this.snack.open('Log deleted', '', { duration: 2000 }); this.loadLogs(); },
        error: (err) => { this.loading = false; this.snack.open(this.readError(err) || 'Delete failed', 'Dismiss', { duration: 3500 }); }
      });
    });
  }

  // ---- Helpers
  trackById(_i: number, r: MaintenanceLog): number { return r.id; }

  formatDate(d?: string | null): string {
    if (!d) return '';
    const s = d.length >= 10 ? d.slice(0, 10) : d; // supports 'YYYY-MM-DDTHH:mm'
    const dt = new Date(s);
    if (isNaN(dt.getTime())) return s;
    const y = dt.getFullYear();
    const m = String(dt.getMonth() + 1).padStart(2, '0');
    const day = String(dt.getDate()).padStart(2, '0');
    return `${y}-${m}-${day}`;
  }

  private readError(err: any): string {
    const e = err?.error ?? err;
    if (typeof e === 'string') return e;
    if (e?.message) return e.message;
    if (e?.error?.message) return e.error.message;
    const bag = e?.errors;
    if (bag && typeof bag === 'object') {
      const k = Object.keys(bag)[0];
      const v = Array.isArray(bag[k]) ? bag[k][0] : bag[k];
      if (v) return `${k}: ${String(v)}`;
    }
    if (err?.status === 400) return 'Validation failed (400). Please check fields.';
    if (err?.status === 403) return 'Forbidden (403). Your role cannot perform this action.';
    if (err?.status === 500) return 'Server error (500). Please try again.';
    return 'Request failed';
  }
}