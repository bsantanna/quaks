import {inject, Signal} from '@angular/core';
import {NavigationEnd, Router} from '@angular/router';
import {toSignal} from '@angular/core/rxjs-interop';
import {filter, map} from 'rxjs';

export class PathReactiveComponent {

  readonly router = inject(Router);

  readonly path!: Signal<string>;
  readonly title!: Signal<string>;


  constructor() {
    this.path = toSignal(
      this.router.events.pipe(
        filter((e): e is NavigationEnd => e instanceof NavigationEnd),
        map(() => {
          let route = this.router.routerState.root;
          while (route.firstChild) route = route.firstChild!;
          return (route.snapshot.url.join('/') as string) || '';
        })
      ),
      {initialValue: ''}
    );

    this.title = toSignal(
      this.router.events.pipe(
        filter((e): e is NavigationEnd => e instanceof NavigationEnd),
        map(() => {
          let route = this.router.routerState.root;
          while (route.firstChild) route = route.firstChild!;
          return (route.snapshot.title as string) || '';
        })
      ),
      {initialValue: ''}
    );

  }

}
