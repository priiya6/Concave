// @vitest-environment jsdom
import {describe,expect,it} from 'vitest';
import {cleanup,render,screen} from '@testing-library/react';
import {afterEach} from 'vitest';
import {StatusBadge} from './components';

describe('StatusBadge',()=>{
  afterEach(cleanup);
  it('renders readable status text',()=>{render(<StatusBadge status="in_progress"/>);expect(screen.getByRole('status').textContent).toBe('in progress')});
  it('preserves escalated meaning in text',()=>{render(<StatusBadge status="escalated"/>);expect(screen.getByRole('status').textContent).toBe('escalated')});
});
