import {Component, input} from '@angular/core';

@Component({
  selector: 'app-small-screen-message',
  imports: [],
  templateUrl: './small-screen-message.html',
  styleUrl: './small-screen-message.scss',
})
export class SmallScreenMessage {
  readonly notice = input.required<string>();
}
