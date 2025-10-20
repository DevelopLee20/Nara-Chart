import React, { useMemo, useState } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

const formatDate = (iso) => new Date(iso).toISOString().slice(0, 10);

const numberFormatter = new Intl.NumberFormat('ko-KR');

const toPercent = (value) => (value == null ? null : Number(value) * 100);

const computeStats = (data, keys) => {
  const stats = {};
  keys.forEach((key) => {
    const values = data
      .map((d) => d[key])
      .filter((v) => typeof v === 'number' && !Number.isNaN(v));
    if (values.length === 0) {
      stats[key] = { avg: null, min: null, max: null };
      return;
    }
    const sum = values.reduce((a, b) => a + b, 0);
    const avg = sum / values.length;
    const min = Math.min(...values);
    const max = Math.max(...values);
    stats[key] = { avg, min, max };
  });
  return stats;
};

export default function TrendChart({ rawData, controlledDateFrom, controlledDateTo }) {
  const [mode, setMode] = useState('amount'); // 'amount' | 'ratio'
  const [checked, setChecked] = useState({
    추정가격: true,
    기초금액: true,
    낙찰금액: true,
    '기초/낙찰': true,
    '추정/낙찰': true,
  });
  const [dateFrom, setDateFrom] = useState(controlledDateFrom || '');
  const [dateTo, setDateTo] = useState(controlledDateTo || '');

  // sync controlled props
  React.useEffect(() => {
    if (controlledDateFrom !== undefined) setDateFrom(controlledDateFrom || '');
  }, [controlledDateFrom]);
  React.useEffect(() => {
    if (controlledDateTo !== undefined) setDateTo(controlledDateTo || '');
  }, [controlledDateTo]);

  const data = useMemo(() => {
    const sorted = [...rawData].sort(
      (a, b) => new Date(a['입찰일']) - new Date(b['입찰일'])
    );
    const filtered = sorted.filter((d) => {
      const iso = formatDate(d['입찰일']);
      if (dateFrom && iso < dateFrom) return false;
      if (dateTo && iso > dateTo) return false;
      return true;
    });
    if (mode === 'amount') return filtered;
    // ratio mode: keep only ratio fields (still keep date and amount fields for tooltip completeness)
    return filtered.map((d) => ({
      ...d,
      '기초/낙찰': toPercent(d['기초/낙찰']),
      '추정/낙찰': toPercent(d['추정/낙찰']),
    }));
  }, [rawData, dateFrom, dateTo, mode]);

  const amountKeys = ['추정가격', '기초금액', '낙찰금액'];
  const ratioKeys = ['기초/낙찰', '추정/낙찰'];

  const visibleKeys = useMemo(
    () => (mode === 'amount' ? amountKeys : ratioKeys).filter((k) => checked[k]),
    [mode, checked]
  );

  const stats = useMemo(
    () => computeStats(data, visibleKeys),
    [data, visibleKeys]
  );

  const colors = {
    추정가격: '#8884d8',
    기초금액: '#82ca9d',
    낙찰금액: '#ff7300',
    '기초/낙찰': '#d62728',
    '추정/낙찰': '#1f77b4',
  };

  const CustomTooltip = ({ active, payload, label }) => {
    if (!active || !payload || payload.length === 0) return null;
    const date = label;
    return (
      <div style={{ background: 'white', border: '1px solid #ddd', padding: 8 }}>
        <div style={{ fontWeight: 600, marginBottom: 6 }}>{date}</div>
        {payload.map((p) => (
          <div key={p.dataKey} style={{ color: p.color, marginBottom: 2 }}>
            {p.name}: {mode === 'amount' ? numberFormatter.format(p.value) : `${p.value.toFixed(3)}%`}
          </div>
        ))}
      </div>
    );
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      {/* Controls */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12, alignItems: 'center' }}>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <label>기간</label>
          <input
            type="date"
            value={dateFrom}
            onChange={(e) => setDateFrom(e.target.value)}
          />
          <span>~</span>
          <input
            type="date"
            value={dateTo}
            onChange={(e) => setDateTo(e.target.value)}
          />
        </div>

        <div style={{ display: 'flex', gap: 8 }}>
          <button
            onClick={() => setMode('amount')}
            style={{
              padding: '6px 10px',
              border: '1px solid #ccc',
              background: mode === 'amount' ? '#333' : '#fff',
              color: mode === 'amount' ? '#fff' : '#333',
              borderRadius: 4,
            }}
          >
            금액
          </button>
          <button
            onClick={() => setMode('ratio')}
            style={{
              padding: '6px 10px',
              border: '1px solid #ccc',
              background: mode === 'ratio' ? '#333' : '#fff',
              color: mode === 'ratio' ? '#fff' : '#333',
              borderRadius: 4,
            }}
          >
            비율(%)
          </button>
        </div>

        <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
          {(mode === 'amount' ? amountKeys : ratioKeys).map((k) => (
            <label key={k} style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
              <input
                type="checkbox"
                checked={!!checked[k]}
                onChange={() => setChecked((prev) => ({ ...prev, [k]: !prev[k] }))}
              />
              {k}
            </label>
          ))}
        </div>
      </div>

      {/* Chart */}
      <div style={{ width: '100%', height: 360 }}>
        <ResponsiveContainer>
          <LineChart data={data} margin={{ top: 10, right: 24, bottom: 10, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey={(d) => formatDate(d['입찰일'])}
              tick={{ fontSize: 12 }}
              minTickGap={24}
            />
            <YAxis
              tickFormatter={(v) => (mode === 'amount' ? numberFormatter.format(v) : `${v.toFixed(3)}%`)}
              tick={{ fontSize: 12 }}
              width={80}
              domain={mode === 'ratio' ? [80, 120] : ['auto', 'auto']}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend />
            {visibleKeys.map((k) => (
              <Line
                key={k}
                type="monotone"
                dataKey={k}
                name={k}
                stroke={colors[k]}
                dot={false}
                strokeWidth={2}
                isAnimationActive={false}
                yAxisId={0}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Stats Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 12 }}>
        {visibleKeys.map((k) => (
          <div key={k} style={{ border: '1px solid #eee', borderRadius: 8, padding: 12 }}>
            <div style={{ fontWeight: 600, marginBottom: 8, color: colors[k] }}>{k}</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              <div>
                <span style={{ color: '#666' }}>평균: </span>
                <strong>
                  {stats[k].avg == null
                    ? '-'
                    : mode === 'amount'
                    ? numberFormatter.format(Math.round(stats[k].avg))
                    : `${stats[k].avg.toFixed(3)}%`}
                </strong>
              </div>
              <div>
                <span style={{ color: '#666' }}>최대: </span>
                <strong>
                  {stats[k].max == null
                    ? '-'
                    : mode === 'amount'
                    ? numberFormatter.format(stats[k].max)
                    : `${stats[k].max.toFixed(3)}%`}
                </strong>
              </div>
              <div>
                <span style={{ color: '#666' }}>최소: </span>
                <strong>
                  {stats[k].min == null
                    ? '-'
                    : mode === 'amount'
                    ? numberFormatter.format(stats[k].min)
                    : `${stats[k].min.toFixed(3)}%`}
                </strong>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}


