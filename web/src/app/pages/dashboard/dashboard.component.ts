// 📄 src/app/pages/dashboard/dashboard.component.ts
import { Component, OnInit, AfterViewInit, inject, ViewChild, ElementRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient, HttpClientModule } from '@angular/common/http';
import { MatTableModule, MatTableDataSource } from '@angular/material/table';
import { MatCardModule } from '@angular/material/card';
import { NgIf } from '@angular/common';
import { Chart } from 'chart.js/auto';
import { environment } from '../../../environments/environment';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, HttpClientModule, MatTableModule, MatCardModule, NgIf],
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.scss'],
})
export class DashboardComponent implements OnInit, AfterViewInit {
  private http = inject(HttpClient);

  @ViewChild('snapshotRoot', { static: false }) snapshotRoot!: ElementRef<HTMLElement>;

  summary: any;
  chart: Chart | undefined;
  dataSource = new MatTableDataSource<any>([]);
  displayedColumns: string[] = ['month', 'cost'];

  ngOnInit(): void {
    this.fetchSummary();
  }

  ngAfterViewInit(): void {}

  fetchSummary(): void {
    this.http.get(`${environment.apiUrl}/api/assets/dashboard-summary`).subscribe({
      next: (res: any) => {
        this.summary = res;
        if (res?.monthly_cost && Array.isArray(res.monthly_cost)) {
          this.renderChart(res.monthly_cost);
          this.dataSource.data = res.monthly_cost;
        }
      },
      error: (err: any) => console.error('Dashboard summary error:', err),
    });
  }

  renderChart(monthlyData: any[]): void {
    const labels = monthlyData.map((item) => item.month);
    const costs = monthlyData.map((item) => item.cost);

    if (this.chart) this.chart.destroy();

    const canvas = document.getElementById('costChart') as HTMLCanvasElement | null;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const gradient = ctx.createLinearGradient(0, 0, 0, canvas.height);
    gradient.addColorStop(0, '#3b82f6');
    gradient.addColorStop(1, '#93c5fd');

    this.chart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels,
        datasets: [
          {
            label: 'Service Cost (₹)',
            data: costs,
            backgroundColor: gradient,
            borderColor: '#1e40af',
            borderWidth: 1,
            borderRadius: 8,
            barThickness: 32,
            hoverBorderWidth: 1,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        layout: { padding: 4 },
        scales: {
          x: {
            border: { display: false },
            grid: { display: false },
            ticks: { color: '#475569', font: { size: 12, weight: 600 } },
          },
          y: {
            border: { display: false },
            grid: { color: 'rgba(148,163,184,0.25)' },
            ticks: {
              color: '#475569',
              font: { size: 12 },
              callback: (value) => `₹${value}`,
            },
          },
        },
        plugins: {
          legend: {
            display: true,
            labels: { color: '#475569', font: { size: 12, weight: 600 }, usePointStyle: true },
          },
          tooltip: {
            backgroundColor: '#0f172a',
            titleColor: '#fff',
            bodyColor: '#e5e7eb',
            cornerRadius: 8,
            padding: 10,
            callbacks: {
              label: (ctx) => ` ₹${ctx.parsed.y?.toLocaleString?.('en-IN') ?? ctx.parsed.y}`,
            },
          },
        },
        animation: { duration: 700, easing: 'easeOutQuart' },
      },
    });
  }

  /** Exports the dashboard container as a crisp PNG image */
  async exportSnapshot(): Promise<void> {
    try {
      if (!this.snapshotRoot?.nativeElement) return;

      // Lazy-load to keep main bundle small
      const html2canvas = (await import('html2canvas')).default;

      // Render at 2x for a sharp image (can raise to 3x on powerful devices)
      const canvas = await html2canvas(this.snapshotRoot.nativeElement, {
        scale: 2,
        backgroundColor: '#f5f7fa', // matches your container bg
        useCORS: true,
        logging: false,
        windowWidth: document.documentElement.scrollWidth,
      });

      const dataUrl = canvas.toDataURL('image/png');
      const a = document.createElement('a');
      const ts = new Date();
      const pad = (n: number) => n.toString().padStart(2, '0');
      const name = `smartasset-dashboard-${ts.getFullYear()}${pad(ts.getMonth() + 1)}${pad(ts.getDate())}-${pad(ts.getHours())}${pad(ts.getMinutes())}.png`;
      a.href = dataUrl;
      a.download = name;
      a.click();
    } catch (e) {
      console.error('Snapshot export failed:', e);
      alert('Sorry, failed to export snapshot. Check console for details.');
    }
  }
}