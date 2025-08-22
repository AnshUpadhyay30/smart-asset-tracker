import { Component, Inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { MatDialogRef, MAT_DIALOG_DATA, MatDialogModule } from '@angular/material/dialog';
import { MatIconModule } from '@angular/material/icon';

@Component({
  standalone: true,
  selector: 'app-confirm-dialog',
  imports: [CommonModule, MatButtonModule, MatDialogModule, MatIconModule], // 👈 dialog + buttons + icon
  templateUrl: './confirm-dialog.component.html',
  styleUrls: ['./confirm-dialog.component.scss'],
})
export class ConfirmDialogComponent {
  constructor(
    private ref: MatDialogRef<ConfirmDialogComponent>,
    @Inject(MAT_DIALOG_DATA)
    public data: { title?: string; message?: string; okText?: string; cancelText?: string }
  ) {}

  onNo(): void { this.ref.close(false); }
  onYes(): void { this.ref.close(true); }
}