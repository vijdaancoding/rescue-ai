import { useState, useEffect } from 'react'
import Layout from '../components/Layout'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  Cell, Legend,
} from 'recharts'
import { TrendingUp, AlertTriangle, CheckCircle, Clock, Phone, Shield, HeartPulse, Flame, Loader2 } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import type { AnalyticsSummary, AnalyticsByDay, AnalyticsDispatch, CallSummary } from '../types'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const URGENCY_ICON: Record<string, React.ReactNode> = {
  critical: <AlertTriangle className="w-5 h-5 text-red-600" />,
  high: <AlertTriangle className="w-5 h-5 text-orange-500" />,
  medium: <Clock className="w-5 h-5 text-yellow-500" />,
  low: <CheckCircle className="w-5 h-5 text-green-500" />,
}

const URGENCY_COLOR_MAP: Record<string, string> = {
  critical: 'text-red-600',
  high: 'text-orange-500',
  medium: 'text-yellow-600',
  low: 'text-green-600',
}

const DISPATCH_ICON_MAP: Record<string, React.ReactNode> = {
  police: <Shield className="w-5 h-5 text-blue-600" />,
  ambulance: <HeartPulse className="w-5 h-5 text-red-500" />,
  firefighters: <Flame className="w-5 h-5 text-orange-500" />,
}

const DISPATCH_COLOR: Record<string, string> = {
  police: '#3b82f6',
  ambulance: '#ef4444',
  firefighters: '#f97316',
}

function StatCard({ label, value, sub, color = 'text-gray-900' }: { label: string; value: string | number; sub?: string; color?: string }) {
  return (
    <div className="card text-center py-5">
      <p className={`text-3xl font-bold mb-1 ${color}`}>{value}</p>
      <p className="text-sm font-medium text-gray-700">{label}</p>
      {sub && <p className="text-xs text-gray-400 mt-0.5">{sub}</p>}
    </div>
  )
}

export default function Analytics() {
  const { token } = useAuth()
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null)
  const [byDay, setByDay] = useState<AnalyticsByDay[]>([])
  const [dispatchBreakdown, setDispatchBreakdown] = useState<AnalyticsDispatch[]>([])
  const [recentCalls, setRecentCalls] = useState<CallSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!token) return
    const headers = { Authorization: `Bearer ${token}` }

    Promise.all([
      fetch(`${API_URL}/api/analytics/summary`, { headers }).then(r => r.json()),
      fetch(`${API_URL}/api/analytics/by-day`, { headers }).then(r => r.json()),
      fetch(`${API_URL}/api/analytics/dispatches`, { headers }).then(r => r.json()),
      fetch(`${API_URL}/calls/?limit=5`, { headers }).then(r => r.json()),
    ])
      .then(([sum, days, dispatches, recent]) => {
        setSummary(sum)
        setByDay(days)
        setDispatchBreakdown(dispatches)
        setRecentCalls(recent)
      })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [token])

  if (loading) {
    return (
      <Layout title="Analytics">
        <div className="flex items-center justify-center h-64 gap-3 text-gray-400">
          <Loader2 className="w-6 h-6 animate-spin" />
          <span>Loading analytics...</span>
        </div>
      </Layout>
    )
  }

  if (error) {
    return (
      <Layout title="Analytics">
        <div className="card text-center py-12">
          <p className="text-red-600 font-medium">{error}</p>
        </div>
      </Layout>
    )
  }

  const spamPct = summary && summary.total_calls > 0
    ? Math.round((summary.spam_calls / summary.total_calls) * 100)
    : 0

  // Format by-day labels to shorter form
  const chartData = byDay.map(d => ({
    ...d,
    label: d.date.slice(5), // "MM-DD"
  }))

  return (
    <Layout title="Analytics">
      <div className="space-y-6">

        {/* Header */}
        <div className="card">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <h2 className="text-2xl font-bold text-gray-900 mb-1">Incident Analytics</h2>
              <p className="text-gray-500 text-sm">Live data from Supabase — call patterns, spam detection, dispatch stats</p>
            </div>
            <button className="btn btn-primary self-start">Export Report</button>
          </div>
        </div>

        {/* Summary stat cards */}
        {summary && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatCard label="Total Calls" value={summary.total_calls} />
            <StatCard label="Real Emergencies" value={summary.real_calls} color="text-green-600" />
            <StatCard label="Spam / Prank" value={summary.spam_calls} sub={`${spamPct}% of all calls`} color="text-red-600" />
            <StatCard label="Dispatched" value={summary.dispatched} color="text-blue-600" />
          </div>
        )}

        {/* Charts */}
        <div className="card">
          <h3 className="text-xl font-bold text-gray-900 mb-1">Incident Response Overview</h3>
          <p className="text-sm text-gray-500 mb-6">Last 30 days — real emergencies vs spam calls per day</p>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Bar chart — calls by day */}
            <div>
              <h4 className="font-semibold text-gray-700 mb-4 flex items-center gap-2 text-sm">
                <TrendingUp className="w-4 h-4 text-teal-500" />
                Real vs Spam by Day
              </h4>
              {chartData.length > 0 ? (
                <ResponsiveContainer width="100%" height={250}>
                  <BarChart data={chartData} barSize={10}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
                    <XAxis dataKey="label" tick={{ fill: '#9ca3af', fontSize: 11 }} />
                    <YAxis tick={{ fill: '#9ca3af', fontSize: 11 }} />
                    <Tooltip contentStyle={{ backgroundColor: '#fff', border: '1px solid #e5e7eb', borderRadius: '8px', fontSize: '12px' }} />
                    <Legend wrapperStyle={{ fontSize: '12px' }} />
                    <Bar dataKey="real" name="Real" fill="#14b8a6" radius={[3, 3, 0, 0]} />
                    <Bar dataKey="spam" name="Spam" fill="#f87171" radius={[3, 3, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-[250px] flex items-center justify-center text-gray-400 text-sm">No data for the last 30 days</div>
              )}
            </div>

            {/* Bar chart — dispatch breakdown */}
            <div>
              <h4 className="font-semibold text-gray-700 mb-4 flex items-center gap-2 text-sm">
                <AlertTriangle className="w-4 h-4 text-orange-500" />
                Dispatch Breakdown by Service
              </h4>
              {dispatchBreakdown.length > 0 ? (
                <ResponsiveContainer width="100%" height={250}>
                  <BarChart data={dispatchBreakdown} layout="vertical" barSize={22}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" horizontal={false} />
                    <XAxis type="number" tick={{ fill: '#9ca3af', fontSize: 11 }} />
                    <YAxis dataKey="dispatch_type" type="category" tick={{ fill: '#6b7280', fontSize: 12 }} width={90} />
                    <Tooltip contentStyle={{ backgroundColor: '#fff', border: '1px solid #e5e7eb', borderRadius: '8px', fontSize: '12px' }} />
                    <Bar dataKey="count" name="Dispatched" radius={[0, 4, 4, 0]}>
                      {dispatchBreakdown.map(entry => (
                        <Cell key={entry.dispatch_type} fill={DISPATCH_COLOR[entry.dispatch_type] ?? '#6b7280'} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-[250px] flex items-center justify-center text-gray-400 text-sm">No dispatch records yet</div>
              )}
            </div>
          </div>
        </div>

        {/* Urgency breakdown */}
        {summary && Object.keys(summary.urgency_breakdown).length > 0 && (
          <div className="card">
            <h3 className="text-lg font-bold text-gray-900 mb-4">Urgency Distribution</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {(['critical', 'high', 'medium', 'low'] as const).map(level => {
                const count = summary.urgency_breakdown[level] ?? 0
                return (
                  <div key={level} className="flex items-center gap-3 p-3 bg-gray-50 rounded-xl">
                    {URGENCY_ICON[level]}
                    <div>
                      <p className={`font-bold text-lg ${URGENCY_COLOR_MAP[level]}`}>{count}</p>
                      <p className="text-xs text-gray-500 capitalize">{level}</p>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        )}

        {/* Recent Calls */}
        <div className="card">
          <h3 className="text-lg font-bold text-gray-900 mb-1">Recent Calls</h3>
          <p className="text-sm text-gray-500 mb-4">Last 5 calls from Supabase</p>

          {recentCalls.length === 0 ? (
            <p className="text-sm text-gray-400 text-center py-6">No calls found</p>
          ) : (
            <div className="space-y-2">
              {recentCalls.map(call => {
                const dt = call.start_time ? new Date(call.start_time) : null
                const isSpam = call.spam_label === 'spam'
                return (
                  <div key={call.id} className="flex items-center gap-4 p-4 bg-gray-50 rounded-xl border border-gray-100">
                    <div className={`w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0 ${
                      isSpam ? 'bg-red-100' : call.urgency_level === 'critical' || call.urgency_level === 'high' ? 'bg-orange-100' : 'bg-teal-100'
                    }`}>
                      {isSpam
                        ? <Phone className="w-5 h-5 text-red-500 line-through" />
                        : (URGENCY_ICON[call.urgency_level ?? 'low'] ?? <CheckCircle className="w-5 h-5 text-teal-500" />)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-semibold text-gray-900 truncate">
                        {call.caller_phone || 'Unknown caller'}
                        {call.caller_country ? ` · ${call.caller_country}` : ''}
                      </p>
                      <p className="text-xs text-gray-400">
                        {dt ? dt.toLocaleString('en-GB', { dateStyle: 'short', timeStyle: 'short' }) : '—'}
                      </p>
                    </div>
                    <div className="flex flex-col items-end gap-1">
                      {call.spam_label && (
                        <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${isSpam ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'}`}>
                          {isSpam ? 'Spam' : 'Real'}
                        </span>
                      )}
                      {call.urgency_level && (
                        <span className={`text-xs font-semibold capitalize ${URGENCY_COLOR_MAP[call.urgency_level] ?? 'text-gray-500'}`}>
                          {call.urgency_level}
                        </span>
                      )}
                      <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                        call.status === 'Dispatched' ? 'bg-blue-100 text-blue-700' :
                        call.status === 'FalseAlarm' ? 'bg-gray-100 text-gray-500' :
                        'bg-yellow-100 text-yellow-700'
                      }`}>
                        {call.status}
                      </span>
                    </div>
                    {call.dispatch_types.length > 0 && (
                      <div className="flex gap-1 flex-shrink-0">
                        {call.dispatch_types.map(t => (
                          <span key={t} title={t}>{DISPATCH_ICON_MAP[t]}</span>
                        ))}
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="text-center text-xs text-gray-400 py-2">
          <p>Confidential — authorized viewing only · © 2026 Rescue AI</p>
        </div>
      </div>
    </Layout>
  )
}
