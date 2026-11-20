import React from 'react';
export function StatusBadge({status}:{status:string}){return <span role="status" className={'pill '+status}>{status.replace('_',' ')}</span>}
