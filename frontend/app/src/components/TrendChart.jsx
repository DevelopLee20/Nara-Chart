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

// EMA 계산 (Exponential Moving Average)
const calculateEMA = (data, key, span = 10) => {
  const alpha = 2 / (span + 1);
  let ema = null;

  return data.map((d) => {
    const value = d[key];
    if (value == null || isNaN(value)) {
      return null;
    }
    if (ema === null) {
      ema = value;
    } else {
      ema = alpha * value + (1 - alpha) * ema;
    }
    return ema;
  });
};

// LOESS 계산 (Locally Weighted Scatterplot Smoothing)
const calculateLOESS = (data, key, bandwidth = 0.3) => {
  const values = data.map(d => d[key]);
  const n = values.length;
  const result = [];

  // 각 점에 대해 로컬 가중 회귀 수행
  for (let i = 0; i < n; i++) {
    const value = values[i];
    if (value == null || isNaN(value)) {
      result.push(null);
      continue;
    }

    // bandwidth 내의 이웃 점들 찾기
    const windowSize = Math.max(3, Math.floor(n * bandwidth));
    const start = Math.max(0, i - Math.floor(windowSize / 2));
    const end = Math.min(n, start + windowSize);

    // 가중치 계산 (tricube weight function)
    let weightedSum = 0;
    let weightSum = 0;

    for (let j = start; j < end; j++) {
      if (values[j] == null || isNaN(values[j])) continue;

      const distance = Math.abs(i - j) / windowSize;
      const weight = Math.pow(1 - Math.pow(distance, 3), 3);

      weightedSum += weight * values[j];
      weightSum += weight;
    }

    result.push(weightSum > 0 ? weightedSum / weightSum : null);
  }

  return result;
};

// 미래 날짜 생성 (3개월, 월단위)
const generateFutureDates = (lastDate, months = 3) => {
  const dates = [];
  const last = new Date(lastDate);

  for (let i = 1; i <= months; i++) {
    const futureDate = new Date(last);
    futureDate.setMonth(futureDate.getMonth() + i);
    dates.push(futureDate.toISOString().slice(0, 10));
  }

  return dates;
};

// EMA 미래 예측
const predictEMA = (lastEMA, months = 3) => {
  // 마지막 EMA 값을 그대로 유지 (평평한 예측)
  return Array(months).fill(lastEMA);
};

// LOESS 미래 예측 (선형 외삽)
const predictLOESS = (loessValues, months = 3) => {
  // 마지막 유효한 값들로 추세 계산
  const validValues = loessValues.filter(v => v != null && !isNaN(v));
  if (validValues.length < 2) return Array(months).fill(validValues[validValues.length - 1] || null);

  // 마지막 5개 값의 평균 기울기 사용
  const lastN = Math.min(5, validValues.length);
  const recentValues = validValues.slice(-lastN);
  const slope = (recentValues[recentValues.length - 1] - recentValues[0]) / (lastN - 1);

  const predictions = [];
  const lastValue = validValues[validValues.length - 1];

  for (let i = 1; i <= months; i++) {
    predictions.push(lastValue + slope * i);
  }

  return predictions;
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
  const [showEMA, setShowEMA] = useState(false);
  const [showLOESS, setShowLOESS] = useState(false);
  const [dateFrom, setDateFrom] = useState(controlledDateFrom || '');
  const [dateTo, setDateTo] = useState(controlledDateTo || '');

  // sync controlled props
  React.useEffect(() => {
    if (controlledDateFrom !== undefined) setDateFrom(controlledDateFrom || '');
  }, [controlledDateFrom]);
  React.useEffect(() => {
    if (controlledDateTo !== undefined) setDateTo(controlledDateTo || '');
  }, [controlledDateTo]);

  const amountKeys = useMemo(() => ['추정가격', '기초금액', '낙찰금액'], []);
  const ratioKeys = useMemo(() => ['기초/낙찰', '추정/낙찰'], []);

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

    let processedData;
    if (mode === 'amount') {
      processedData = filtered;
    } else {
      // ratio mode: keep only ratio fields (still keep date and amount fields for tooltip completeness)
      processedData = filtered.map((d) => ({
        ...d,
        '기초/낙찰': toPercent(d['기초/낙찰']),
        '추정/낙찰': toPercent(d['추정/낙찰']),
      }));
    }

    // EMA와 LOESS 계산 및 추가
    const keysToProcess = mode === 'amount' ? amountKeys : ratioKeys;
    const emaByKey = {};
    const loessByKey = {};

    keysToProcess.forEach((key) => {
      if (showEMA) {
        const emaValues = calculateEMA(processedData, key, 10);
        emaByKey[key] = emaValues;
        processedData = processedData.map((d, i) => ({
          ...d,
          [`${key}_EMA`]: emaValues[i],
        }));
      }
      if (showLOESS) {
        const loessValues = calculateLOESS(processedData, key, 0.3);
        loessByKey[key] = loessValues;
        processedData = processedData.map((d, i) => ({
          ...d,
          [`${key}_LOESS`]: loessValues[i],
        }));
      }
    });

    // 미래 날짜 추가 (EMA 또는 LOESS가 활성화된 경우)
    if ((showEMA || showLOESS) && processedData.length > 0) {
      const lastDate = processedData[processedData.length - 1]['입찰일'];
      const futureDates = generateFutureDates(lastDate, 3);

      futureDates.forEach((futureDate, idx) => {
        const futurePoint = {
          '입찰일': futureDate,
          추정가격: null,
          기초금액: null,
          낙찰금액: null,
          '기초/낙찰': null,
          '추정/낙찰': null,
        };

        keysToProcess.forEach((key) => {
          if (showEMA && emaByKey[key]) {
            const lastEMA = emaByKey[key][emaByKey[key].length - 1];
            const predictions = predictEMA(lastEMA, 3);
            futurePoint[`${key}_EMA`] = predictions[idx];
          }
          if (showLOESS && loessByKey[key]) {
            const predictions = predictLOESS(loessByKey[key], 3);
            futurePoint[`${key}_LOESS`] = predictions[idx];
          }
        });

        processedData.push(futurePoint);
      });
    }

    return processedData;
  }, [rawData, dateFrom, dateTo, mode, showEMA, showLOESS, amountKeys, ratioKeys]);

  const visibleKeys = useMemo(
    () => (mode === 'amount' ? amountKeys : ratioKeys).filter((k) => checked[k]),
    [mode, checked, amountKeys, ratioKeys]
  );

  const stats = useMemo(
    () => computeStats(data, visibleKeys),
    [data, visibleKeys]
  );

  const colors = {
    추정가격: '#3b82f6',  // 파란색
    기초금액: '#10b981',  // 녹색
    낙찰금액: '#f59e0b',  // 주황색
    '기초/낙찰': '#ef4444',  // 빨간색
    '추정/낙찰': '#8b5cf6',  // 보라색
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

        <div style={{ display: 'flex', gap: 12, alignItems: 'center', marginLeft: 'auto' }}>
          <label style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
            <input
              type="checkbox"
              checked={showEMA}
              onChange={() => setShowEMA(!showEMA)}
            />
            EMA
          </label>
          <label style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
            <input
              type="checkbox"
              checked={showLOESS}
              onChange={() => setShowLOESS(!showLOESS)}
            />
            LOESS
          </label>
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
                opacity={showEMA || showLOESS ? 0.2 : 1}
              />
            ))}
            {showEMA && visibleKeys.map((k) => (
              <Line
                key={`${k}_EMA`}
                type="monotone"
                dataKey={`${k}_EMA`}
                name={`${k} EMA`}
                stroke={colors[k]}
                strokeDasharray="5 5"
                dot={false}
                strokeWidth={2.5}
                isAnimationActive={false}
                yAxisId={0}
                connectNulls={true}
              />
            ))}
            {showLOESS && visibleKeys.map((k) => (
              <Line
                key={`${k}_LOESS`}
                type="monotone"
                dataKey={`${k}_LOESS`}
                name={`${k} LOESS`}
                stroke={colors[k]}
                strokeDasharray="10 5"
                dot={false}
                strokeWidth={3}
                isAnimationActive={false}
                yAxisId={0}
                connectNulls={true}
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


