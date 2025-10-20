const API_BASE = process.env.REACT_APP_API_BASE || process.env.REACT_APP_API_URL || '';

export async function fetchBids({ skip = 0, limit = 200 } = {}) {
  const url = new URL(`${API_BASE}/api/bids/`, window.location.origin);
  url.searchParams.set('skip', String(skip));
  url.searchParams.set('limit', String(limit));
  const res = await fetch(url.toString(), {
    headers: { 'Accept': 'application/json' },
    credentials: 'include',
  });
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`Failed to fetch bids: ${res.status} ${text}`);
  }
  const json = await res.json();
  return json; // { total, items }
}

export async function searchBids({ keyword, organization, industry, region, bid_date_from, bid_date_to, skip = 0, limit = 200 } = {}) {
  const url = new URL(`${API_BASE}/api/bids/search`, window.location.origin);
  if (keyword) url.searchParams.set('keyword', keyword);
  if (organization) url.searchParams.set('organization', organization);
  if (industry) url.searchParams.set('industry', industry);
  if (region) url.searchParams.set('region', region);
  if (bid_date_from) url.searchParams.set('bid_date_from', bid_date_from);
  if (bid_date_to) url.searchParams.set('bid_date_to', bid_date_to);
  url.searchParams.set('skip', String(skip));
  url.searchParams.set('limit', String(limit));
  const res = await fetch(url.toString(), {
    headers: { 'Accept': 'application/json' },
    credentials: 'include',
  });
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`Failed to search bids: ${res.status} ${text}`);
  }
  return await res.json();
}

export async function fetchOrganizations() {
  const url = new URL(`${API_BASE}/api/bids/filters/organizations`, window.location.origin);
  const res = await fetch(url.toString(), { headers: { 'Accept': 'application/json' }, credentials: 'include' });
  if (!res.ok) throw new Error(`Failed to fetch organizations: ${res.status}`);
  return await res.json();
}

export async function fetchIndustries() {
  const url = new URL(`${API_BASE}/api/bids/filters/industries`, window.location.origin);
  const res = await fetch(url.toString(), { headers: { 'Accept': 'application/json' }, credentials: 'include' });
  if (!res.ok) throw new Error(`Failed to fetch industries: ${res.status}`);
  return await res.json();
}

export async function fetchRegions() {
  const url = new URL(`${API_BASE}/api/bids/filters/regions`, window.location.origin);
  const res = await fetch(url.toString(), { headers: { 'Accept': 'application/json' }, credentials: 'include' });
  if (!res.ok) throw new Error(`Failed to fetch regions: ${res.status}`);
  return await res.json();
}

export function mapBidToTrendItem(b) {
  return {
    '입찰일': b.bid_date,
    '추정가격': b.estimated_price ?? null,
    '기초금액': b.base_price ?? null,
    '낙찰금액': b.winning_price ?? null,
    '기초/낙찰': b.base_winning_rate ?? null,
    '추정/낙찰': b.estimated_winning_rate ?? null,
  };
}

