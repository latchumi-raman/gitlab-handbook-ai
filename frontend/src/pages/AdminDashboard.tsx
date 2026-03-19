import { useQuery }       from "@tanstack/react-query";
import { Link }           from "react-router-dom";
import {
  MessageSquare, ThumbsUp, Database,
  TrendingUp, Shield, ArrowLeft, RefreshCw,
} from "lucide-react";

import { fetchAnalyticsSummary, fetchConfidenceDistribution } from "@/lib/api";
import { formatConfidence } from "@/lib/utils";

import { StatsCard }          from "@/components/analytics/StatsCard";
import { QueriesChart }       from "@/components/analytics/QueriesChart";
import { FeedbackChart }      from "@/components/analytics/FeedbackChart";
import { ConfidenceGauge }    from "@/components/analytics/ConfidenceGauge";
import { TopQueriesTable }    from "@/components/analytics/TopQueriesTable";
import { SourcesBreakdown }   from "@/components/analytics/SourcesBreakdown";
import { useTheme }           from "@/hooks/useTheme";
import { Button }             from "@/components/ui/Button";
import { Moon, Sun }          from "lucide-react";

export function AdminDashboard() {
  const { toggle, isDark } = useTheme();

  const {
    data: summary, isLoading: summaryLoading, refetch: refetchSummary,
  } = useQuery({
    queryKey:        ["analytics-summary"],
    queryFn:         fetchAnalyticsSummary,
    refetchInterval: 60_000,
  });

  const { data: confidenceData } = useQuery({
    queryKey: ["analytics-confidence"],
    queryFn:  fetchConfidenceDistribution,
  });

  const isLoading = summaryLoading;

  const feedbackScore = summary
    ? summary.total_feedback > 0
      ? Math.round((summary.positive_feedback / summary.total_feedback) * 100)
      : null
    : null;

  return (
    <div className="min-h-screen bg-surface-50 dark:bg-surface-950">
      {/* Top bar */}
      <header className="sticky top-0 z-10 bg-white dark:bg-surface-950 border-b border-surface-200 dark:border-surface-800 px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link to="/" className="flex items-center gap-1.5 text-sm text-gray-500 dark:text-gray-400 hover:text-gitlab-orange transition-colors">
            <ArrowLeft size={14} />
            Back to chat
          </Link>
          <span className="text-surface-200 dark:text-surface-700">|</span>
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-md bg-gradient-to-br from-gitlab-orange to-gitlab-red flex items-center justify-center">
              <span className="text-white font-bold text-xs">GL</span>
            </div>
            <span className="font-semibold text-gray-800 dark:text-gray-100 text-sm">
              Analytics Dashboard
            </span>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="sm" onClick={() => refetchSummary()} title="Refresh">
            <RefreshCw size={14} className={isLoading ? "animate-spin" : ""} />
          </Button>
          <Button variant="ghost" size="sm" onClick={toggle}>
            {isDark ? <Sun size={14} /> : <Moon size={14} />}
          </Button>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-8 space-y-8">
        {/* ── Stats row ── */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <StatsCard
            label="Total queries"
            value={isLoading ? "—" : (summary?.total_queries ?? 0).toLocaleString()}
            sub={`${summary?.queries_last_7_days ?? 0} this week`}
            icon={<MessageSquare size={18} />}
            accent="orange"
          />
          <StatsCard
            label="Avg confidence"
            value={isLoading ? "—" : formatConfidence(summary?.avg_confidence ?? 0)}
            sub="Across all queries"
            icon={<TrendingUp size={18} />}
            accent={
              (summary?.avg_confidence ?? 0) >= 0.7 ? "green"
              : (summary?.avg_confidence ?? 0) >= 0.5 ? "blue"
              : "red"
            }
          />
          <StatsCard
            label="Feedback score"
            value={feedbackScore !== null ? `${feedbackScore}%` : "—"}
            sub={`${summary?.total_feedback ?? 0} ratings total`}
            icon={<ThumbsUp size={18} />}
            accent={feedbackScore !== null && feedbackScore >= 70 ? "green" : "orange"}
          />
          <StatsCard
            label="Guardrail rate"
            value={isLoading ? "—" : formatConfidence(summary?.guardrail_rate ?? 0)}
            sub="Off-topic queries blocked"
            icon={<Shield size={18} />}
            accent="purple"
          />
        </div>

        {/* ── Queries over time + Sources ── */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 bg-white dark:bg-surface-900 rounded-2xl border border-surface-200 dark:border-surface-800 p-5">
            <h3 className="text-sm font-semibold text-gray-800 dark:text-gray-100 mb-4">
              Queries over time (last 30 days)
            </h3>
            {isLoading
              ? <div className="h-48 animate-pulse bg-surface-100 dark:bg-surface-800 rounded-xl" />
              : <QueriesChart data={summary?.queries_per_day ?? []} />
            }
          </div>

          <div className="bg-white dark:bg-surface-900 rounded-2xl border border-surface-200 dark:border-surface-800 p-5">
            <h3 className="text-sm font-semibold text-gray-800 dark:text-gray-100 mb-1">
              Indexed sources
            </h3>
            <p className="text-xs text-gray-400 dark:text-gray-500 mb-4">
              {(summary?.chunks_indexed ?? 0).toLocaleString()} total chunks
            </p>
            <SourcesBreakdown
              handbookChunks  = {summary?.handbook_chunks  ?? 0}
              directionChunks = {summary?.direction_chunks ?? 0}
              total           = {summary?.chunks_indexed   ?? 1}
            />
            <div className="mt-4 pt-4 border-t border-surface-100 dark:border-surface-800">
              <div className="flex items-center gap-1.5">
                <Database size={13} className="text-gray-400" />
                <span className="text-xs text-gray-400 dark:text-gray-500">
                  Stored in Supabase pgvector
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* ── Feedback + Confidence histogram ── */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white dark:bg-surface-900 rounded-2xl border border-surface-200 dark:border-surface-800 p-5">
            <h3 className="text-sm font-semibold text-gray-800 dark:text-gray-100 mb-1">
              User feedback
            </h3>
            <p className="text-xs text-gray-400 dark:text-gray-500 mb-2">
              {summary?.positive_feedback ?? 0} helpful · {summary?.negative_feedback ?? 0} not helpful
            </p>
            <FeedbackChart
              positive={summary?.positive_feedback ?? 0}
              negative={summary?.negative_feedback ?? 0}
            />
          </div>

          <div className="bg-white dark:bg-surface-900 rounded-2xl border border-surface-200 dark:border-surface-800 p-5">
            <h3 className="text-sm font-semibold text-gray-800 dark:text-gray-100 mb-1">
              Confidence distribution
            </h3>
            <p className="text-xs text-gray-400 dark:text-gray-500 mb-4">
              Similarity score buckets across all queries
            </p>
            <ConfidenceGauge data={confidenceData ?? []} />
          </div>
        </div>

        {/* ── Top queries ── */}
        <div className="bg-white dark:bg-surface-900 rounded-2xl border border-surface-200 dark:border-surface-800 p-5">
          <h3 className="text-sm font-semibold text-gray-800 dark:text-gray-100 mb-4">
            Most popular queries (last 30 days)
          </h3>
          {isLoading
            ? <div className="space-y-3">
                {Array.from({ length: 5 }).map((_, i) => (
                  <div key={i} className="h-8 animate-pulse bg-surface-100 dark:bg-surface-800 rounded-lg" />
                ))}
              </div>
            : <TopQueriesTable queries={summary?.top_queries ?? []} />
          }
        </div>
      </main>
    </div>
  );
}