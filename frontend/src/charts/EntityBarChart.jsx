import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";

export default function EntityBarChart({ title, data }) {
  const chartData = data.slice(0, 8).map((item) => ({
    name: item.entity_name,
    score: item.trend_score
  }));

  return (
    <section className="panel chart-panel">
      <h2>{title}</h2>
      <ResponsiveContainer width="100%" height={280}>
        <BarChart data={chartData}>
          <CartesianGrid stroke="#d8dedb" strokeDasharray="3 3" />
          <XAxis dataKey="name" tick={{ fontSize: 12 }} interval={0} height={70} />
          <YAxis />
          <Tooltip />
          <Bar dataKey="score" fill="#158f7a" radius={[6, 6, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </section>
  );
}
