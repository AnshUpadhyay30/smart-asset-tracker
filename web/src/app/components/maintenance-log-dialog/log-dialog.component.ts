// src/app/components/maintenance-log-dialog/log-dialog.component.ts
import { Component, Inject, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MAT_DIALOG_DATA, MatDialogRef, MatDialogModule } from '@angular/material/dialog';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatNativeDateModule } from '@angular/material/core';
import { MatIconModule } from '@angular/material/icon';

type DialogMode = 'create' | 'edit';

@Component({
  standalone: true,
  selector: 'app-log-dialog',
  templateUrl: './log-dialog.component.html',
  styleUrls: ['./log-dialog.component.scss'],
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
  ],
})
export class LogDialogComponent {
  private fb = inject(FormBuilder);
  private dialogRef = inject(MatDialogRef<LogDialogComponent>);

  submitting = false;

  constructor(
    @Inject(MAT_DIALOG_DATA)
    public data: { mode: DialogMode; assetId?: number; log?: any }
  ) {}

  // Strongly-typed controls (datepicker = Date)
  form = this.fb.group({
    service_date: this.fb.control<Date | null>(new Date(), { validators: Validators.required }),
    description:   this.fb.control<string>('', { validators: [Validators.required, Validators.minLength(2)] }),
    parts_used:    this.fb.control<string>(''),
    cost:          this.fb.control<string>('0'), // input type=number returns string
    next_service_due: this.fb.control<Date | null>(null),
  });

  ngOnInit() {
    if (this.data?.mode === 'edit' && this.data.log) {
      const l = this.data.log;
      this.form.patchValue({
        service_date: l.service_date ? new Date(l.service_date) : new Date(),
        description: (l.description ?? '').toString(),
        parts_used: (l.parts_used ?? '').toString(),
        cost: (typeof l.cost === 'number' ? l.cost : Number(l.cost ?? 0)).toString(),
        next_service_due: l.next_service_due ? new Date(l.next_service_due) : null,
      });
    }
  }

  private ymd(d: Date | null): string | null {
    if (!d) return null;
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${y}-${m}-${day}`;
  }

  save() {
    if (this.form.invalid) { this.form.markAllAsTouched(); return; }
    this.submitting = true;

    const v = this.form.value;
    const payload: any = {
      service_date: this.ymd(v.service_date!)!,              // ✅ required by backend
      description: (v.description ?? '').toString().trim(),  // ✅ non-empty
      parts_used: (v.parts_used ?? '').toString().trim() || null,
      cost: Number(v.cost ?? 0),                              // ✅ number (backend Numeric)
    };
    if (v.next_service_due) payload.next_service_due = this.ymd(v.next_service_due);

    // Note: assetId path me hai; body me bhejna जरूरी नहीं
    this.dialogRef.close(payload);
  }

  cancel() { this.dialogRef.close(null); }
}