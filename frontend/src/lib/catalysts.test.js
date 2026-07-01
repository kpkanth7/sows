import test from 'node:test';
import assert from 'node:assert/strict';
import { buildEventMap, getUpcomingCatalyst } from './catalysts.js';

test('buildEventMap matches events by company ids, names, and tickers', () => {
  const companies = [
    { id: '1', name: 'Anthropic', ticker: null },
    { id: '2', name: 'Microsoft', ticker: 'MSFT' },
  ];
  const rows = [
    { event_name: 'Anthropic Dev Summit', event_date: '2026-07-20', event_type: 'conference', company_ids: ['1'], company_names: [] },
    { event_name: 'Microsoft Build Regional', event_date: '2026-08-01', event_type: 'conference', company_ids: [], company_names: ['MSFT'] },
  ];

  const map = buildEventMap(rows, companies);

  assert.equal(map.get('1')[0].event_name, 'Anthropic Dev Summit');
  assert.equal(map.get('2')[0].event_name, 'Microsoft Build Regional');
});

test('getUpcomingCatalyst prefers actual event calendar entries over earnings', () => {
  const company = { id: '1', name: 'Anthropic', ticker: null, recent_event: null, recent_event_date: null };
  const eventMap = new Map([
    ['1', [{ event_name: 'Anthropic Dev Summit', event_date: '2099-07-20', event_type: 'conference' }]],
  ]);

  const catalyst = getUpcomingCatalyst({
    company,
    eventMap,
    earnings: [{ earnings_date: '2099-07-10' }],
  });

  assert.equal(catalyst.kind, 'event');
  assert.equal(catalyst.label, 'conference · 2099-07-20');
});
