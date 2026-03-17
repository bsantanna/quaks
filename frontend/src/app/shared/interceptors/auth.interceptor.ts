import {HttpHandlerFn, HttpInterceptorFn, HttpRequest} from '@angular/common/http';
import {inject} from '@angular/core';
import {catchError, from, switchMap, throwError} from 'rxjs';
import {AuthService} from '../services/auth.service';
import {environment} from '../../../environments/environment';

export const authInterceptor: HttpInterceptorFn = (
  req: HttpRequest<unknown>,
  next: HttpHandlerFn,
) => {
  const authService = inject(AuthService);

  // Skip interceptor for Keycloak requests and auth endpoints
  if (req.url.startsWith(environment.keycloakUrl) ||
      req.url.includes('/auth/exchange') ||
      req.url.includes('/auth/renew')) {
    return next(req);
  }

  const token = authService.getAccessToken();
  const authedReq = token
    ? req.clone({setHeaders: {Authorization: `Bearer ${token}`}})
    : req;

  return next(authedReq).pipe(
    catchError(error => {
      if (error.status === 401 && authService.state()) {
        return from(authService.renewToken()).pipe(
          switchMap(renewed => {
            if (renewed) {
              const newToken = authService.getAccessToken();
              if (!newToken) return throwError(() => error);
              const retryReq = req.clone({
                setHeaders: {Authorization: `Bearer ${newToken}`},
              });
              return next(retryReq);
            }
            return throwError(() => error);
          }),
        );
      }
      return throwError(() => error);
    }),
  );
};
