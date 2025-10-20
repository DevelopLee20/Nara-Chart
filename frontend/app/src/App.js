import './App.css';
import TrendChart from './components/TrendChart';
import { fetchBids, searchBids, mapBidToTrendItem, fetchOrganizations, fetchIndustries, fetchRegions } from './api/bids';
import { useEffect, useState } from 'react';

function useBidsTrendData({ keyword, organization, industry, region, bidDateFrom, bidDateTo }) {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        setLoading(true);
        const hasSearch = keyword || organization || industry || region;
        const res = hasSearch || bidDateFrom || bidDateTo
          ? await searchBids({ keyword, organization, industry, region, bid_date_from: bidDateFrom, bid_date_to: bidDateTo, skip: 0, limit: 500 })
          : await fetchBids({ skip: 0, limit: 500 });
        const mapped = (res.items || []).map(mapBidToTrendItem);
        if (mounted) setData(mapped);
      } catch (e) {
        if (mounted) setError(e);
      } finally {
        if (mounted) setLoading(false);
      }
    })();
    return () => {
      mounted = false;
    };
  }, [keyword, organization, industry, region, bidDateFrom, bidDateTo]);

  return { data, loading, error };
}

function App() {
  const [keyword, setKeyword] = useState('');
  const [organization, setOrganization] = useState('');
  const [industry, setIndustry] = useState('');
  const [region, setRegion] = useState('');
  const [debouncedKeyword, setDebouncedKeyword] = useState(keyword);
  const [bidDateFrom, setBidDateFrom] = useState('');
  const [bidDateTo, setBidDateTo] = useState('');
  const [orgOptions, setOrgOptions] = useState([]);
  const [industryOptions, setIndustryOptions] = useState([]);
  const [regionOptions, setRegionOptions] = useState([]);
  useEffect(() => {
    const t = setTimeout(() => setDebouncedKeyword(keyword), 400);
    return () => clearTimeout(t);
  }, [keyword]);
  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const [orgs, inds, regs] = await Promise.all([
          fetchOrganizations(),
          fetchIndustries(),
          fetchRegions(),
        ]);
        if (!mounted) return;
        setOrgOptions(orgs || []);
        setIndustryOptions(inds || []);
        setRegionOptions(regs || []);
      } catch (e) {
        // 옵션 로딩 실패는 치명적이지 않음
      }
    })();
    return () => {
      mounted = false;
    };
  }, []);
  const { data, loading, error } = useBidsTrendData({ keyword: debouncedKeyword, organization, industry, region, bidDateFrom, bidDateTo });
  return (
    <div className="App" style={{ padding: 20, maxWidth: 1200, margin: '0 auto' }}>
      <h2 style={{ textAlign: 'left', marginBottom: 16 }}>입찰 추세선</h2>
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr 1fr 1fr', gap: 8, marginBottom: 12 }}>
        <input value={keyword} placeholder="키워드" onChange={(e) => setKeyword(e.target.value)} />
        <select value={organization} onChange={(e) => setOrganization(e.target.value)}>
          <option value="">발주기관(전체)</option>
          {orgOptions.map((o) => (
            <option key={o} value={o}>{o}</option>
          ))}
        </select>
        <select value={industry} onChange={(e) => setIndustry(e.target.value)}>
          <option value="">업종(전체)</option>
          {industryOptions.map((o) => (
            <option key={o} value={o}>{o}</option>
          ))}
        </select>
        <select value={region} onChange={(e) => setRegion(e.target.value)}>
          <option value="">지역(전체)</option>
          {regionOptions.map((o) => (
            <option key={o} value={o}>{o}</option>
          ))}
        </select>
      </div>
      <div style={{ display: 'flex', gap: 8, marginBottom: 12, alignItems: 'center' }}>
        <label>입찰일</label>
        <input type="date" value={bidDateFrom} onChange={(e) => setBidDateFrom(e.target.value)} />
        <span>~</span>
        <input type="date" value={bidDateTo} onChange={(e) => setBidDateTo(e.target.value)} />
      </div>
      {error && (
        <div style={{ color: 'crimson', marginBottom: 12 }}>
          데이터를 불러오지 못했습니다: {String(error.message || error)}
        </div>
      )}
      {loading ? (
        <div style={{ color: '#666' }}>불러오는 중…</div>
      ) : (
        <TrendChart rawData={data} />
      )}
    </div>
  );
}

export default App;
