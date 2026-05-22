import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";

export default function ForecastLineChart({ forecasts }) {
  const chartData = forecasts.slice(0, 14).map((item) => ({
    name: `${item.entity_name} h${item.horizon}`,
    value: item.predicted_value
  }));

  return (
    <section className="panel chart-panel">
      <h2>Forecast Movement</h2>
      <ResponsiveContainer width="100%" height={280}>
        <LineChart data={chartData}>
          <CartesianGrid stroke="#d8dedb" strokeDasharray="3 3" />
          <XAxis dataKey="name" tick={{ fontSize: 12 }} height={70} />
          <YAxis />
          <Tooltip />
          <Line type="monotone" dataKey="value" stroke="#d0385f" strokeWidth={3} dot={{ r: 3 }} />
        </LineChart>
      </ResponsiveContainer>
    </section>
  );
}
