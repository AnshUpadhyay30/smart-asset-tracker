// src/app/pages/reports/reports.component.ts
import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';

// ✅ standalone directive instead of NgChartsModule
import { BaseChartDirective } from 'ng2-charts';
import { ChartData, ChartOptions, ChartType } from 'chart.js';

import { MatTableModule } from '@angular/material/table';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule }   from '@angular/material/icon';
import { MatSelectModule } from '@angular/material/select';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatTooltipModule } from '@angular/material/tooltip';

import { ReportsService, ExpiringAsset, MonthlyCost } from './reports.service';

@Component({
  standalone: true,
  selector: 'app-reports',
  templateUrl: './reports.component.html',
  styleUrls: ['./reports.component.scss'],
  imports: [
    CommonModule,
    // ✅ use directive here
    BaseChartDirective,
    // table + ui
    MatTableModule, MatButtonModule, MatIconModule,
    MatSelectModule, MatFormFieldModule, MatProgressBarModule, MatTooltipModule
  ]
})
export class ReportsComponent {
  private api = inject(ReportsService);

  // UI state
  loadingCost = signal(false);
  loadingWarranty = signal(false);
  errorCost = signal<string | null>(null);
  errorWarranty = signal<string | null>(null);

  // Warranty filter
  daysOptions = [30, 60, 90];
  selectedDays = signal(30);

  // Warranty table
  expiring: ExpiringAsset[] = [];
  displayed = ['name', 'category', 'warranty_end'];

  // Chart
  chartType: ChartType = 'bar';
  monthLabels: string[] = [];
  chartData: ChartData<'bar'> = {
    labels: this.monthLabels,
    datasets: [{ label: 'Maintenance Cost', data: [], borderWidth: 2 }]
  };
  chartOptions: ChartOptions<'bar'> = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { labels: { boxWidth: 12 } },
      tooltip: { mode: 'index', intersect: false }
    },
    scales: {
      x: { grid: { display: false } },
      y: { ticks: { callback: (v) => `₹${v}` as any } }
    }
  };

  ngOnInit() {
    this.loadMonthlyCost();
    this.loadWarranty();
  }

  // ----- API calls -----
  loadMonthlyCost() {
    this.loadingCost.set(true);
    this.errorCost.set(null);
    this.api.getMonthlyCost().subscribe({
      next: (rows) => this.bindChart(rows),
      error: () => this.errorCost.set('Failed to load monthly cost'),
      complete: () => this.loadingCost.set(false)
    });
  }

  loadWarranty() {
    this.loadingWarranty.set(true);
    this.errorWarranty.set(null);
    this.api.getWarrantyExpiring(this.selectedDays()).subscribe({
      next: (rows) => (this.expiring = rows || []),
      error: () => this.errorWarranty.set('Failed to load warranty data'),
      complete: () => this.loadingWarranty.set(false)
    });
  }

  onDaysChange(v: number) {
    this.selectedDays.set(v);
    this.loadWarranty();
  }

  // ----- CSV downloads -----
  downloadAssetsCsv() {
    this.api.downloadAssetsCsv().subscribe(blob => this.saveBlob(blob, `assets_${this.today()}.csv`));
  }
  downloadLogsCsv() {
    this.api.downloadLogsCsv().subscribe(blob => this.saveBlob(blob, `maintenance_${this.today()}.csv`));
  }
  private saveBlob(blob: Blob, filename: string) {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = filename; a.click();
    URL.revokeObjectURL(url);
  }

  // ----- helpers -----
  private bindChart(rows: MonthlyCost[]) {
    // Sort input
    const ordered = [...rows].sort((a, b) =>
      a.year !== b.year ? a.year - b.year : a.month - b.month
    );

    // Build a map (year-month -> cost)
    const costMap = new Map<string, number>();
    let minY = Number.POSITIVE_INFINITY, minM = 12, maxY = 0, maxM = 1;

    for (const r of ordered) {
      const key = `${r.year}-${String(r.month).padStart(2, '0')}`;
      costMap.set(key, Number(r.total_cost || 0));
      if (r.year < minY || (r.year === minY && r.month < minM)) { minY = r.year; minM = r.month; }
      if (r.year > maxY || (r.year === maxY && r.month > maxM)) { maxY = r.year; maxM = r.month; }
    }

    // If API returned only sparse months (e.g., Jan & Aug), pad the range so July shows up as ₹0
    const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
    this.monthLabels.length = 0;
    const data: number[] = [];

    // guard: if no data, nothing to show
    if (!isFinite(minY)) {
      this.chartData = { labels: [], datasets: [{ label: 'Maintenance Cost', data: [], borderWidth: 2 }] };
      return;
    }

    // iterate month-by-month from min -> max
    let y = minY, m = minM;
    while (y < maxY || (y === maxY && m <= maxM)) {
      const key = `${y}-${String(m).padStart(2, '0')}`;
      this.monthLabels.push(`${months[m - 1]} ${String(y).slice(-2)}`);
      data.push(costMap.get(key) ?? 0);

      // increment month
      m++;
      if (m > 12) { m = 1; y++; }
    }

    this.chartData = {
      labels: this.monthLabels,
      datasets: [{
        label: 'Maintenance Cost',
        data,
        borderWidth: 2,
        // light fill for subtle corporate feel
        backgroundColor: 'rgba(37, 99, 235, 0.25)',
        borderColor: 'rgba(37, 99, 235, 0.8)'
      }]
    };

    // Optional: subtle grid/ticks polish (client-only)
    this.chartOptions = {
      responsive: true, maintainAspectRatio: false,
      plugins: {
        legend: { labels: { boxWidth: 12 } },
        tooltip: { mode: 'index', intersect: false }
      },
      scales: {
        x: { grid: { color: 'rgba(2,6,23,.06)' } },
        y: {
          grid: { color: 'rgba(2,6,23,.08)' },
          ticks: { callback: (v) => `₹${v}` as any }
        }
      }
    };
  }

  private today() {
    return new Date().toISOString().slice(0,10);
  }
}