// @vitest-environment jsdom
import {describe,expect,it,vi} from 'vitest';
import {cleanup,render,screen} from '@testing-library/react';
import {afterEach} from 'vitest';
import {StatusBadge,HistoryPanel,SavedReplyPicker,InternalTicketPanel,SavedRepliesAdmin,NotificationList} from './components';

describe('StatusBadge',()=>{
  afterEach(cleanup);
  it('renders readable status text',()=>{render(<StatusBadge status="in_progress"/>);expect(screen.getByRole('status').textContent).toBe('in progress')});
  it('preserves escalated meaning in text',()=>{render(<StatusBadge status="escalated"/>);expect(screen.getByRole('status').textContent).toBe('escalated')});
});

describe('bonus panels',()=>{
  afterEach(()=>{cleanup();vi.restoreAllMocks();localStorage.clear()});
  it('renders history actor and reason',()=>{render(<HistoryPanel events={[{id:1,event_type:'priority_changed',actor:{name:'Arjun'},old_value:'low',new_value:'high',reason:'Payment risk',created_at:'2026-01-01T10:00:00Z'}]}/>);expect(screen.getByText('priority changed')).toBeTruthy();expect(screen.getByText('Arjun')).toBeTruthy();expect(screen.getByText(/Payment risk/)).toBeTruthy()});
  it('loads and inserts a saved reply',async()=>{vi.stubGlobal('fetch',vi.fn().mockResolvedValue({ok:true,json:async()=>({items:[{id:1,title:'Greeting',body:'Thanks for contacting us.'}]})}));const onSelect=vi.fn();render(<SavedReplyPicker onSelect={onSelect}/>);await screen.findByText('Greeting');await import('@testing-library/react').then(({fireEvent})=>fireEvent.change(screen.getByRole('combobox'),{target:{value:'1'}}));expect(onSelect).toHaveBeenCalledWith('Thanks for contacting us.')});
  it('validates internal ticket creation fields',()=>{render(<InternalTicketPanel ticket={{ticket_number:'TKT-0001',version:1,internal_tickets:[]}} onUpdate={()=>{}}/>);expect((screen.getByRole('button',{name:'Create internal ticket'}) as HTMLButtonElement).disabled).toBe(true)});
  it('shows saved reply admin form',()=>{vi.stubGlobal('fetch',vi.fn().mockResolvedValue({ok:true,json:async()=>({items:[]})}));render(<SavedRepliesAdmin/>);expect(screen.getByRole('heading',{name:'Saved replies'})).toBeTruthy();expect((screen.getByRole('button',{name:'Create saved reply'}) as HTMLButtonElement).disabled).toBe(true)});
  it('marks a notification when selected',()=>{const onRead=vi.fn();render(<NotificationList items={[{id:7,message:'TKT-0007 escalated',ticket_id:7,is_read:false,created_at:'2026-01-01T10:00:00Z'}]} onRead={onRead}/>);screen.getByRole('button',{name:/TKT-0007 escalated/}).click();expect(onRead).toHaveBeenCalledWith(7)});
});
