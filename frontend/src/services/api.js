import axios from "axios";

const client = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000",
  timeout: 12000
});

export async function getDashboardData(filters) {
  const params = {};
  if (filters.source !== "all") {
    params.source = filters.source;
  }

  const [tech, companies, summaries, forecasts, sources] = await Promise.all([
    client.get("/trends/technologies", { params }),
    client.get("/trends/companies", { params }),
    client.get("/summaries/latest"),
    client.get("/forecasts/top"),
    client.get("/sources/status")
  ]);

  return {
    technologies: tech.data,
    companies: companies.data,
    summaries: summaries.data,
    forecasts: forecasts.data,
    sources: sources.data
  };
}
