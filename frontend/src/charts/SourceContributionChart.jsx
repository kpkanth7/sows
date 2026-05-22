import {
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip
} from "recharts";

const colors = ["#158f7a", "#d0385f", "#f0c33c", "#3f7fca", "#6f8d3d", "#2b2b2b"];

export default function SourceContributionChart({ technologies, companies }) {
  const counts = [...technologies, ...companies].reduce((acc, item) => {
    acc[item.source_name] = (acc[item.source_name] || 0) + item.trend_score;
    return acc;
  }, {});
  const data = Object.entries(counts).map(([name, value]) => ({ name, value }));

  return (
    <section className="panel chart-panel">
      <h2>Source Contributions</h2>
      <ResponsiveContainer width="100%" height={280}>
        <PieChart>
          <Pie data={data} dataKey="value" nameKey="name" outerRadius={95} label>
            {data.map((entry, index) => (
              <Cell key={entry.name} fill={colors[index % colors.length]} />
            ))}
          </Pie>
          <Tooltip />
        </PieChart>
      </ResponsiveContainer>
    </section>
  );
}
