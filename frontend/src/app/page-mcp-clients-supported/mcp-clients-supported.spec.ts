import { ComponentFixture, TestBed } from '@angular/core/testing';

import { McpClientsSupported } from './mcp-clients-supported';

describe('McpClientsSupported', () => {
  let component: McpClientsSupported;
  let fixture: ComponentFixture<McpClientsSupported>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [McpClientsSupported]
    })
    .compileComponents();

    fixture = TestBed.createComponent(McpClientsSupported);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
