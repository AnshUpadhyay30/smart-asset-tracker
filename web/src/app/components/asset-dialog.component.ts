// 📄 src/app/components/asset-dialog.component.ts
import { Component, Inject, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';

import { MatDialogRef, MatDialogModule, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatNativeDateModule } from '@angular/material/core';
import { MatIconModule } from '@angular/material/icon';

type AssetDialogData = {
  id?: number;
  name?: string;
  category?: string;
  location?: string;
  purchase_date?: string | Date | null;
};

@Component({
  standalone: true,
  selector: 'app-asset-dialog',
  templateUrl: './asset-dialog.component.html',
  styleUrls: ['./asset-dialog.component.scss'],
  imports: [
    CommonModule,
    ReactiveFormsModule,
    MatDialogModule,
    MatFormFieldModule,
    MatInputModule,
    MatButtonModule,
    MatDatepickerModule,
    MatNativeDateModule,
    MatIconModule
  ]
})
export class AssetDialogComponent {
  private fb = inject(FormBuilder);
  private dialogRef = inject(MatDialogRef<AssetDialogComponent>);

  // Required fields align with backend schema (name, category, location, purchase_date)
  form: FormGroup = this.fb.group({
    name: ['', Validators.required],
    category: ['', Validators.required],
    location: ['', Validators.required],
    purchase_date: [null, Validators.required], // Date object in control
  });

  isEdit = false;

  constructor(@Inject(MAT_DIALOG_DATA) public data: AssetDialogData | null) {
    this.isEdit = !!data?.id;
    if (data) {
      this.form.patchValue({
        name: data.name ?? '',
        category: data.category ?? '',
        location: data.location ?? '',
        purchase_date: this.toDate(data.purchase_date),
      });
    }
  }

  private toDate(v: string | Date | null | undefined): Date | null {
    if (!v) return null;
    if (v instanceof Date) return v;
    const s = typeof v === 'string' && v.length >= 10 ? v.slice(0, 10) : String(v);
    const d = new Date(s);
    return isNaN(d.getTime()) ? null : d;
  }

  private fmt(d: Date | null): string | null {
    if (!d) return null;
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${y}-${m}-${day}`; // YYYY-MM-DD (backend compatible)
  }

  save(): void {
    if (this.form.invalid) return;

    const raw = this.form.value as {
      name: string; category: string; location: string; purchase_date: Date | null;
    };

    const payload = {
      ...(this.isEdit && this.data?.id ? { id: this.data.id } : {}),
      name: (raw.name ?? '').toString().trim(),
      category: (raw.category ?? '').toString().trim(),
      location: (raw.location ?? '').toString().trim(),
      purchase_date: this.fmt(raw.purchase_date),
    };

    this.dialogRef.close(payload);
  }
}