import React from 'react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend } from 'recharts';

const TrendChart = ({ history }) => {
  if (!history || history.length < 3) return null;

  // Chronological order for chart
  const data = [...history].reverse().map(item => ({
    date: item.screened_at.substring(0, 10),
    highRiskProb: item.risk_probabilities?.High || 0,
    label: item.risk_label
  }));

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div style={{ background: '#fff', padding: '10px', border: '1px solid #ccc', borderRadius: '4px', fontFamily: 'var(--sans)' }}>
          <p style={{ margin: 0, fontWeight: 600 }}>{label}</p>
          <p style={{ margin: '4px 0 0 0', color: 'var(--ink)', fontFamily: 'var(--mono)' }}>
            High Risk Prob: {(payload[0].value * 100).toFixed(1)}%
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div style={{ width: '100%', height: 300 }}>
      <ResponsiveContainer>
        <LineChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 10 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(0,0,0,0.05)" />
          <XAxis 
            dataKey="date" 
            tick={{ fontFamily: 'var(--mono)', fontSize: 12, fill: 'var(--ink)' }} 
            axisLine={false} 
            tickLine={false} 
          />
          <YAxis 
            tick={{ fontFamily: 'var(--mono)', fontSize: 12, fill: 'var(--ink)' }}
            tickFormatter={(val) => `${(val * 100).toFixed(0)}%`}
            axisLine={false} 
            tickLine={false} 
            domain={[0, 1]}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend wrapperStyle={{ fontFamily: 'var(--sans)', fontSize: 14 }} />
          <Line 
            type="monotone" 
            dataKey="highRiskProb" 
            name="High Risk Probability" 
            stroke="var(--ink)" 
            strokeWidth={3} 
            dot={{ r: 5, fill: "var(--ink)" }} 
            activeDot={{ r: 7 }} 
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default TrendChart;
