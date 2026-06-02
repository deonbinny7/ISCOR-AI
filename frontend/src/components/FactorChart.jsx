import React from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';


const FactorChart = ({ factors }) => {
  if (!factors || factors.length === 0) return null;

  const data = factors.map(f => ({
    name: f.feature.replace(/_/g, ' '),
    value: Math.abs(f.shap_value),
    rawShap: f.shap_value,
    direction: f.direction,
    featureKey: f.feature,
    color: f.direction === 'increases_risk' ? 'var(--amber)' : 'var(--sage)'
  })).sort((a, b) => a.value - b.value); // Sort ascending by magnitude

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div style={{ background: '#fff', padding: '10px', border: '1px solid #ccc', borderRadius: '4px', fontFamily: 'var(--sans)' }}>
          <p style={{ margin: 0, fontWeight: 600 }}>{data.name}</p>
          <p style={{ margin: '4px 0 0 0', fontFamily: 'var(--mono)' }}>
            Impact: {data.rawShap > 0 ? '+' : ''}{data.rawShap.toFixed(3)}
          </p>
          <p style={{ margin: '4px 0 0 0', fontSize: '0.85rem', color: data.direction === 'increases_risk' ? 'var(--amber)' : 'var(--sage)' }}>
            {data.direction === 'increases_risk' ? 'Increases Risk' : 'Decreases Risk'}
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div style={{ width: '100%', height: Math.max(200, factors.length * 45) }}>
      <ResponsiveContainer>
        <BarChart
          data={data}
          layout="vertical"
          margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
        >
          <XAxis type="number" hide />
          <YAxis 
            dataKey="name" 
            type="category" 
            axisLine={false} 
            tickLine={false} 
            tick={{ fontFamily: 'var(--sans)', fontSize: 13, fill: 'var(--ink)' }}
            width={120}
          />
          <Tooltip content={<CustomTooltip />} />
          <Bar dataKey="value" radius={[0, 4, 4, 0]}>
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};

export default FactorChart;
