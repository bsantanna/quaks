import { ComponentFixture, TestBed } from '@angular/core/testing';

import { McpServerSupported } from './mcp-server-supported';

describe('McpServerSupported', () => {
  let component: McpServerSupported;
  let fixture: ComponentFixture<McpServerSupported>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [McpServerSupported]
    })
    .compileComponents();

    fixture = TestBed.createComponent(McpServerSupported);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
