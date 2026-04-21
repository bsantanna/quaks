import { ComponentFixture, TestBed } from '@angular/core/testing';

import { McpClientsClaude } from './mcp-clients-claude';

describe('McpClientsClaude', () => {
  let component: McpClientsClaude;
  let fixture: ComponentFixture<McpClientsClaude>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [McpClientsClaude]
    })
    .compileComponents();

    fixture = TestBed.createComponent(McpClientsClaude);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
