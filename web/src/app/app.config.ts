// 📄 src/app/app.config.ts

import { ApplicationConfig } from '@angular/core';
import {
  provideHttpClient,
  withInterceptorsFromDi,
  HTTP_INTERCEPTORS
} from '@angular/common/http';
import { provideRouter } from '@angular/router';
import { provideCharts } from 'ng2-charts';

import { routes } from './app.routes';
import { AuthInterceptor } from './core/interceptors/auth.interceptor';

// ✅ Add this for MatDatepicker to work properly
import { provideNativeDateAdapter } from '@angular/material/core';

export const appConfig: ApplicationConfig = {
  providers: [
    // ✅ Enable HttpClient with DI support
    provideHttpClient(withInterceptorsFromDi()),

    // ✅ Use legacy style for interceptor registration (Angular 15/16/17)
    {
      provide: HTTP_INTERCEPTORS,
      useClass: AuthInterceptor,
      multi: true,
    },

    // ✅ Provide router and charting
    provideRouter(routes),
    provideCharts(),

    // ✅ Fix for MatDatepicker error (DateAdapter missing)
    provideNativeDateAdapter()
  ],
};