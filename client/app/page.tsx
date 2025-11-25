'use client';

import { FormEvent, useEffect, useMemo, useRef, useState } from "react";
import axios from "axios";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
  PieChart,
  Pie,
  Legend,
  LineChart,
  Line,
  CartesianGrid,
} from "recharts";
import {
  Briefcase,
  MapPin,
  Code,
  TrendingUp,
  Search,
  ExternalLink,
} from "lucide-react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";
const COLORS = [
  "#6366f1",
  "#8b5cf6",
  "#d946ef",
  "#f43f5e",
  "#f97316",
  "#10b981",
  "#14b8a6",
  "#0ea5e9",
];

type SkillDatum = { name: string; value: number };
type CityDatum = SkillDatum;

type Job = {
  id?: string | number;
  title?: string;
  company?: string;
  location?: string;
  searched_city?: string;
  searched_role?: string;
  extracted_skills?: string[];
  date_posted?: string;
  job_url?: string;
};

type DashboardStats = {
  jobs: Job[];
  skills: SkillDatum[];
  cities: CityDatum[];
  total: number;
};

type HistoryTrends = {
  skills: string[];
  data: { month: string; [key: string]: number | string }[];
};

const DEFAULT_STATE: DashboardStats = {
  jobs: [],
  skills: [],
  cities: [],
  total: 0,
};

const DEFAULT_HISTORY: HistoryTrends = {
  skills: [],
  data: [],
};

export default function Dashboard() {
  const [stats, setStats] = useState<DashboardStats>(DEFAULT_STATE);
  const [history, setHistory] = useState<HistoryTrends>(DEFAULT_HISTORY);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [useSemanticSearch, setUseSemanticSearch] = useState(false);
  const [semanticResults, setSemanticResults] = useState<Job[]>([]);
  const [semanticLoading, setSemanticLoading] = useState(false);
  const [subscriberEmail, setSubscriberEmail] = useState("");
  const [subscriberKeyword, setSubscriberKeyword] = useState("");
  const [subscribeStatus, setSubscribeStatus] = useState<{ type: "success" | "error"; message: string } | null>(null);
  const [subscribeLoading, setSubscribeLoading] = useState(false);
  const initialLoad = useRef(true);

  useEffect(() => {
    let isMounted = true;
    const fetchData = async () => {
      try {
        const [jobsRes, skillsRes, citiesRes, historyRes] = await Promise.all([
          axios.get(`${API_URL}/jobs?limit=50`),
          axios.get(`${API_URL}/trends/skills`),
          axios.get(`${API_URL}/trends/cities`),
          axios.get(`${API_URL}/trends/history`),
        ]);

        if (!isMounted) {
          return;
        }

        setStats({
          jobs: jobsRes.data.data ?? [],
          total: jobsRes.data.total ?? 0,
          skills: skillsRes.data ?? [],
          cities: citiesRes.data ?? [],
        });
        setHistory(historyRes.data ?? DEFAULT_HISTORY);

        if (initialLoad.current) {
          setLoading(false);
          initialLoad.current = false;
        }
      } catch (error) {
        console.error("Error connecting to API:", error);
        if (initialLoad.current) {
          setLoading(false);
          initialLoad.current = false;
        }
      }
    };

    fetchData();
    const interval = setInterval(() => {
      console.log("♻️ Refreshing dashboard data...");
      fetchData();
    }, 60000);

    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  // Semantic search effect
  useEffect(() => {
    if (!useSemanticSearch || !searchTerm.trim()) {
      setSemanticResults([]);
      return;
    }

    const timeoutId = setTimeout(async () => {
      setSemanticLoading(true);
      try {
        const response = await axios.get(`${API_URL}/jobs/search`, {
          params: { query: searchTerm, limit: 20 },
        });
        setSemanticResults(response.data.data || []);
      } catch (error) {
        console.error("Semantic search failed:", error);
        setSemanticResults([]);
        // Fall back to keyword search if semantic search fails
        setUseSemanticSearch(false);
      } finally {
        setSemanticLoading(false);
      }
    }, 500); // Debounce for 500ms

    return () => clearTimeout(timeoutId);
  }, [searchTerm, useSemanticSearch]);

  const filteredJobs = useMemo(() => {
    if (useSemanticSearch && searchTerm.trim()) {
      return semanticResults;
    }
    const term = searchTerm.toLowerCase();
    if (!term) return stats.jobs;
    return stats.jobs.filter((job) => {
      const haystack = `${job.title ?? ""} ${job.company ?? ""}`.toLowerCase();
      return haystack.includes(term);
    });
  }, [stats.jobs, searchTerm, useSemanticSearch, semanticResults]);

  const handleSubscribe = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSubscribeStatus(null);

    if (!subscriberEmail || !subscriberKeyword) {
      setSubscribeStatus({ type: "error", message: "Please provide both email and keyword." });
      return;
    }

    try {
      setSubscribeLoading(true);
      const response = await axios.post(`${API_URL}/subscribe`, {
        email: subscriberEmail,
        keyword: subscriberKeyword,
      });
      setSubscribeStatus({ type: "success", message: response.data?.message ?? "Subscription saved!" });
      setSubscriberEmail("");
      setSubscriberKeyword("");
    } catch (error: unknown) {
      const fallback = "Could not save your subscription. Please try again.";
      if (axios.isAxiosError(error)) {
        const detail = (error.response?.data as { detail?: string })?.detail;
        setSubscribeStatus({ type: "error", message: detail ?? fallback });
      } else {
        setSubscribeStatus({ type: "error", message: fallback });
      }
    } finally {
      setSubscribeLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center text-white">
        <div className="animate-pulse flex flex-col items-center">
          <div className="h-12 w-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mb-4" />
          <p>Loading Market Data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-8 font-sans">
      <header className="mb-10 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
            Morocco Tech Monitor
          </h1>
          <p className="text-slate-400 mt-1">Real-time Job Market Intelligence</p>
        </div>
        <div className="flex items-center gap-2 bg-slate-900 px-4 py-2 rounded-lg border border-slate-800">
          <div className="h-3 w-3 rounded-full bg-green-500 animate-pulse" />
          <span className="text-sm font-medium text-green-400">System Live</span>
        </div>
      </header>

      <section className="bg-slate-900 border border-slate-800 rounded-xl p-6 mb-10 shadow-lg">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6 mb-4">
          <div>
            <p className="text-sm font-semibold tracking-wide text-blue-400 uppercase">New</p>
            <h2 className="text-2xl font-semibold text-white mt-1">Let the jobs come to you</h2>
            <p className="text-slate-400 text-sm mt-1">
              Subscribe once and receive email alerts whenever we scrape fresh roles that mention your favorite skill.
            </p>
          </div>
          <div className="hidden md:flex items-center gap-2 text-sm text-slate-400">
            <div className="h-2 w-2 rounded-full bg-blue-500 animate-pulse" />
            Real-time alerts powered by Resend
          </div>
        </div>
        <form className="flex flex-col md:flex-row gap-4" onSubmit={handleSubscribe}>
          <input
            type="email"
            placeholder="Email address"
            className="flex-1 bg-slate-950 border border-slate-800 rounded-lg px-4 py-3 text-sm focus:outline-none focus:border-blue-500"
            value={subscriberEmail}
            onChange={(event) => setSubscriberEmail(event.target.value)}
            required
          />
          <input
            type="text"
            placeholder='Keyword (e.g. "React")'
            className="flex-1 bg-slate-950 border border-slate-800 rounded-lg px-4 py-3 text-sm focus:outline-none focus:border-blue-500"
            value={subscriberKeyword}
            onChange={(event) => setSubscriberKeyword(event.target.value)}
            required
          />
          <button
            type="submit"
            className="bg-blue-600 hover:bg-blue-500 transition text-white font-semibold rounded-lg px-6 py-3 disabled:opacity-50 disabled:cursor-not-allowed"
            disabled={subscribeLoading}
          >
            {subscribeLoading ? "Subscribing..." : "Subscribe"}
          </button>
        </form>
        {subscribeStatus && (
          <p
            className={`text-sm mt-4 ${
              subscribeStatus.type === "success" ? "text-green-400" : "text-amber-400"
            }`}
          >
            {subscribeStatus.message}
          </p>
        )}
      </section>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
        <KpiCard
          title="Total Active Jobs"
          value={stats.total}
          icon={<Briefcase className="text-blue-400" />}
        />
        <KpiCard
          title="Top Skill"
          value={stats.skills[0]?.name ?? "N/A"}
          icon={<Code className="text-purple-400" />}
          subValue={`${stats.skills[0]?.value ?? 0} mentions`}
        />
        <KpiCard
          title="Top Hub"
          value={stats.cities[0]?.name ?? "N/A"}
          icon={<MapPin className="text-pink-400" />}
          subValue={`${stats.cities[0]?.value ?? 0} postings`}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-10">
        <div className="bg-slate-900 p-6 rounded-xl border border-slate-800 shadow-lg">
          <div className="flex items-center gap-2 mb-6">
            <TrendingUp className="text-blue-500" size={20} />
            <h2 className="text-xl font-semibold">Top 10 In-Demand Skills</h2>
          </div>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={stats.skills} layout="vertical" margin={{ left: 20 }}>
                <XAxis type="number" hide />
                <YAxis
                  dataKey="name"
                  type="category"
                  width={100}
                  tick={{ fill: "#94a3b8" }}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#1e293b",
                    borderColor: "#334155",
                    color: "#fff",
                  }}
                  cursor={{ fill: "transparent" }}
                />
                <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                  {stats.skills.map((entry, index) => (
                    <Cell key={`skill-${entry.name}-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-slate-900 p-6 rounded-xl border border-slate-800 shadow-lg">
          <div className="flex items-center gap-2 mb-6">
            <MapPin className="text-purple-500" size={20} />
            <h2 className="text-xl font-semibold">Job Distribution by City</h2>
          </div>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={stats.cities}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  paddingAngle={5}
                  dataKey="value"
            >
                  {stats.cities.map((entry, index) => (
                    <Cell key={`city-${entry.name}-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#1e293b",
                    borderColor: "#334155",
                    color: "#fff",
                  }}
                />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="bg-slate-900 p-6 rounded-xl border border-slate-800 shadow-lg mb-10">
        <div className="flex items-center gap-2 mb-6">
          <TrendingUp className="text-green-400" size={20} />
          <h2 className="text-xl font-semibold">Historical Skill Trends</h2>
        </div>
        <p className="text-slate-400 text-sm mb-4">
          Track how the demand for top skills evolves month over month.
        </p>
        <div className="h-80">
          {history.data.length ? (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={history.data}>
                <CartesianGrid stroke="#1e293b" strokeDasharray="4 4" />
                <XAxis dataKey="month" stroke="#475569" />
                <YAxis stroke="#475569" allowDecimals={false} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#0f172a",
                    borderColor: "#1e293b",
                    color: "#fff",
                  }}
                />
                {history.skills.map((skillName, index) => (
                  <Line
                    key={`line-${skillName}`}
                    type="monotone"
                    dataKey={skillName}
                    stroke={COLORS[index % COLORS.length]}
                    strokeWidth={2}
                    dot={false}
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-full flex items-center justify-center text-slate-500 text-sm">
              Not enough historical data yet. Please check back after the next refresh.
            </div>
          )}
        </div>
      </div>

      <div className="bg-slate-900 rounded-xl border border-slate-800 shadow-lg overflow-hidden">
        <div className="p-6 border-b border-slate-800 flex flex-col sm:flex-row justify-between items-center gap-4">
          <h2 className="text-xl font-semibold">Recent Opportunities</h2>
          <div className="flex items-center gap-3">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-2.5 text-slate-500 h-4 w-4" />
              <input
                type="text"
                placeholder={useSemanticSearch ? "AI-powered search (e.g., 'Machine Learning')..." : "Search companies or roles..."}
                className="bg-slate-950 border border-slate-700 rounded-lg pl-10 pr-4 py-2 text-sm focus:outline-none focus:border-blue-500 w-64 text-slate-300"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
              {semanticLoading && (
                <div className="absolute right-3 top-2.5">
                  <div className="h-4 w-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
                </div>
              )}
            </div>
            <button
              onClick={() => setUseSemanticSearch(!useSemanticSearch)}
              className={`px-3 py-2 rounded-lg text-xs font-medium transition-colors ${
                useSemanticSearch
                  ? "bg-purple-600 hover:bg-purple-500 text-white"
                  : "bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700"
              }`}
              title={useSemanticSearch ? "Using AI semantic search" : "Enable AI semantic search"}
            >
              {useSemanticSearch ? "🧠 AI" : "🔍 Keyword"}
            </button>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-400">
            <thead className="bg-slate-950 text-slate-200 uppercase text-xs font-medium">
              <tr>
                <th className="px-6 py-4">Job Title</th>
                <th className="px-6 py-4">Company</th>
                <th className="px-6 py-4">City</th>
                <th className="px-6 py-4">Posted</th>
                <th className="px-6 py-4">Skills Detected</th>
                <th className="px-6 py-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {filteredJobs.slice(0, 10).map((job, idx) => {
                const visibleSkills = job.extracted_skills?.slice(0, 3) ?? [];
                return (
                  <tr key={`${job.title}-${idx}`} className="hover:bg-slate-800/50 transition-colors">
                    <td className="px-6 py-4 font-medium text-white">{job.title ?? "N/A"}</td>
                    <td className="px-6 py-4">{job.company ?? "—"}</td>
                    <td className="px-6 py-4">{job.searched_city ?? job.location ?? "Unknown"}</td>
                    <td className="px-6 py-4">{formatDate(job.date_posted)}</td>
                    <td className="px-6 py-4">
                      <div className="flex flex-wrap gap-1">
                        {visibleSkills.map((skill) => (
                          <span
                            key={`${job.title}-${skill}`}
                            className="px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-400 text-xs border border-blue-500/20"
                          >
                            {skill}
                          </span>
                        ))}
                        {visibleSkills.length === 0 && <span className="text-xs text-slate-500">No tags yet</span>}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-right">
                      {job.job_url ? (
                        <a
                          href={job.job_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1 text-blue-400 hover:text-blue-300 hover:underline"
                        >
                          Apply <ExternalLink size={14} />
                        </a>
                      ) : (
                        <span className="text-slate-500 text-xs">No link</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

type KpiCardProps = {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  subValue?: string;
};

function formatDate(value?: string) {
  if (!value) return "—";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.valueOf())) {
    return value;
  }
  return parsed.toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function KpiCard({ title, value, icon, subValue }: KpiCardProps) {
  return (
    <div className="bg-slate-900 p-6 rounded-xl border border-slate-800 shadow-lg flex items-center justify-between">
      <div>
        <p className="text-slate-400 text-sm font-medium uppercase">{title}</p>
        <h3 className="text-3xl font-bold mt-1 text-white">{value}</h3>
        {subValue && <p className="text-slate-500 text-xs mt-1">{subValue}</p>}
      </div>
      <div className="p-4 bg-slate-950 rounded-full border border-slate-800">{icon}</div>
    </div>
  );
}
