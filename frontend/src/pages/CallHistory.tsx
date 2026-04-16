import { useState, useEffect, useCallback } from 'react'
import Layout from '../components/Layout'
import { Phone, PhoneOff, Clock, Calendar, Filter, Search, Shield, HeartPulse, Flame, Loader2, Download } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import type { CallSummary } from '../types'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const URGENCY_BADGE: Record<string, string> = {
  critical: 'bg-red-100 text-red-700 dark:bg-red-500/15 dark:text-red-400',
  high:     'bg-orange-100 text-orange-700 dark:bg-orange-500/15 dark:text-orange-400',
  medium:   'bg-amber-100 text-amber-700 dark:bg-amber-500/15 dark:text-amber-400',
  low:      'bg-emerald-100 text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-400',
}

const STATUS_BADGE: Record<string, string> = {
  Dispatched: 'bg-blue-100 text-blue-700 dark:bg-blue-500/15 dark:text-blue-400',
  FalseAlarm: 'bg-slate-100 text-slate-500 dark:bg-zinc-800 dark:text-zinc-500',
  Active:     'bg-emerald-100 text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-400',
  Incoming:   'bg-amber-100 text-amber-700 dark:bg-amber-500/15 dark:text-amber-400',
}

const DISPATCH_ICON: Record<string, React.ReactNode> = {
  police:      <Shield   className="w-3.5 h-3.5 text-blue-600 dark:text-blue-400" aria-label="Police" />,
  ambulance:   <HeartPulse className="w-3.5 h-3.5 text-red-600 dark:text-red-400" aria-label="Ambulance" />,
  firefighters:<Flame    className="w-3.5 h-3.5 text-orange-600 dark:text-orange-400" aria-label="Firefighters" />,
}

function formatDuration(seconds: number | null): string {
  if (seconds == null) return '—'
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m}:${s.toString().padStart(2, '0')}`
}

function formatDateTime(iso: string | null): { date: string; time: string } {
  if (!iso) return { date: '—', time: '—' }
  const d = new Date(iso)
  return {
    date: d.toLocaleDateString('en-GB'),
    time: d.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' }),
  }
}

export default function CallHistory() {
  const { token } = useAuth()
  const [calls, setCalls] = useState<CallSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [spamFilter, setSpamFilter] = useState('')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')

  const fetchCalls = useCallback(async () => {
    if (!token) return
    setLoading(true)
    setError(null)
    try {
      const params = new URLSearchParams()
      if (statusFilter) params.set('status', statusFilter)
      if (spamFilter) params.set('spam_label', spamFilter)
      if (dateFrom) params.set('date_from', dateFrom)
      if (dateTo) params.set('date_to', dateTo)
      if (search) params.set('search', search)
      params.set('limit', '100')

      const res = await fetch(`${API_URL}/calls/?${params.toString()}`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      setCalls(await res.json())
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Error loading calls')
    } finally {
      setLoading(false)
    }
  }, [token, statusFilter, spamFilter, dateFrom, dateTo, search])

  useEffect(() => {
    const id = setTimeout(fetchCalls, 300)
    return () => clearTimeout(id)
  }, [fetchCalls])

  const totalCalls  = calls.length
  const realCalls   = calls.filter(c => c.spam_label === 'not_spam').length
  const spamCalls   = calls.filter(c => c.spam_label === 'spam').length
  const dispatched  = calls.filter(c => c.status === 'Dispatched').length

  const filterInputCls = `w-full pl-9 pr-4 py-2 rounded-lg text-sm transition-all
    bg-white border border-slate-200 text-slate-900 placeholder:text-slate-400
    dark:bg-zinc-800 dark:border-zinc-700 dark:text-zinc-200
    focus:outline-none focus:ring-1 focus:ring-teal-500 dark:focus:ring-cyan-500 focus:border-teal-500 dark:focus:border-cyan-500`

  const dateInputCls = `flex-1 px-2 py-2 rounded-lg text-xs transition-all
    bg-white border border-slate-200 text-slate-700
    dark:bg-zinc-800 dark:border-zinc-700 dark:text-zinc-300
    focus:outline-none focus:ring-1 focus:ring-teal-500 dark:focus:ring-cyan-500 focus:border-teal-500 dark:focus:border-cyan-500`

  return (
    <Layout title="Call History">
      <div className="space-y-5">

        {/* Header */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="text-base font-semibold text-slate-800 dark:text-zinc-200">Call History Log</h2>
            <p className="text-xs text-slate-400 dark:text-zinc-500 mt-0.5">Complete record from Supabase</p>
          </div>
          <button className="btn btn-secondary flex items-center gap-2 self-start text-xs py-2">
            <Download className="w-3.5 h-3.5" />
            Export CSV
          </button>
        </div>

        {/* Stats row */}
        {!loading && !error && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {[
              { label: 'Total Calls',       value: totalCalls,  color: 'text-slate-900 dark:text-zinc-100' },
              { label: 'Real Emergencies',  value: realCalls,   color: 'text-emerald-600 dark:text-emerald-400' },
              { label: 'Prank / Spam',      value: spamCalls,   color: 'text-red-600 dark:text-red-400' },
              { label: 'Dispatched',        value: dispatched,  color: 'text-blue-600 dark:text-blue-400' },
            ].map(stat => (
              <div key={stat.label} className="card py-4 text-center">
                <p className={`text-2xl font-bold tabular ${stat.color}`}>{stat.value}</p>
                <p className="text-xs text-slate-400 dark:text-zinc-600 mt-1">{stat.label}</p>
              </div>
            ))}
          </div>
        )}

        {/* Filters */}
        <div className="card py-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-2.5">
            <div className="relative lg:col-span-2">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-400 dark:text-zinc-500 pointer-events-none" />
              <input
                type="text"
                placeholder="Search phone or city..."
                value={search}
                onChange={e => setSearch(e.target.value)}
                className={filterInputCls}
              />
            </div>

            <div className="relative">
              <Filter className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-400 dark:text-zinc-500 pointer-events-none" />
              <select
                value={statusFilter}
                onChange={e => setStatusFilter(e.target.value)}
                className={`${filterInputCls} appearance-none`}
              >
                <option value="">All Statuses</option>
                <option value="Active">Active</option>
                <option value="Dispatched">Dispatched</option>
                <option value="FalseAlarm">False Alarm</option>
                <option value="Incoming">Incoming</option>
              </select>
            </div>

            <div className="relative">
              <Shield className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-400 dark:text-zinc-500 pointer-events-none" />
              <select
                value={spamFilter}
                onChange={e => setSpamFilter(e.target.value)}
                className={`${filterInputCls} appearance-none`}
              >
                <option value="">All Types</option>
                <option value="not_spam">Real Emergencies</option>
                <option value="spam">Prank / Spam</option>
              </select>
            </div>

            <div className="flex gap-1.5 items-center">
              <input type="date" value={dateFrom} onChange={e => setDateFrom(e.target.value)} className={dateInputCls} />
              <span className="text-slate-300 dark:text-zinc-600 text-xs">–</span>
              <input type="date" value={dateTo} onChange={e => setDateTo(e.target.value)} className={dateInputCls} />
            </div>
          </div>
        </div>

        {/* Table */}
        <div className="card overflow-x-auto p-0">
          {loading ? (
            <div className="flex items-center justify-center py-16 gap-3 text-slate-400 dark:text-zinc-600">
              <Loader2 className="w-4 h-4 animate-spin" />
              <span className="text-sm">Loading calls...</span>
            </div>
          ) : error ? (
            <div className="text-center py-12">
              <p className="text-red-600 dark:text-red-400 text-sm">{error}</p>
            </div>
          ) : calls.length === 0 ? (
            <div className="text-center py-12">
              <Phone className="w-10 h-10 text-slate-300 dark:text-zinc-700 mx-auto mb-3" />
              <p className="text-slate-400 dark:text-zinc-600 text-sm">No calls match your filters</p>
            </div>
          ) : (
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-200 dark:border-zinc-800">
                  {['Date & Time', 'Duration', 'Phone / Location', 'AI Signal', 'Dispatched', 'Status'].map(h => (
                    <th key={h} className="text-left py-3 px-5 text-[10px] font-semibold text-slate-400 dark:text-zinc-600 uppercase tracking-widest">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {calls.map(call => {
                  const { date, time } = formatDateTime(call.start_time)
                  const isSpam = call.spam_label === 'spam'
                  return (
                    <tr key={call.id} className="border-b border-slate-100 dark:border-zinc-800/50 hover:bg-slate-50 dark:hover:bg-zinc-800/30 transition-colors">
                      <td className="py-3.5 px-5">
                        <div className="flex items-center gap-2">
                          <Calendar className="w-3.5 h-3.5 text-slate-300 dark:text-zinc-600 flex-shrink-0" />
                          <div>
                            <p className="text-sm font-medium text-slate-800 dark:text-zinc-200 tabular">{date}</p>
                            <p className="text-xs text-slate-400 dark:text-zinc-600 tabular">{time}</p>
                          </div>
                        </div>
                      </td>
                      <td className="py-3.5 px-5">
                        <div className="flex items-center gap-1.5 text-sm text-slate-500 dark:text-zinc-400">
                          <Clock className="w-3 h-3 text-slate-300 dark:text-zinc-600" />
                          <span className="tabular">{formatDuration(call.duration_seconds)}</span>
                        </div>
                      </td>
                      <td className="py-3.5 px-5">
                        <p className="text-sm text-slate-700 dark:text-zinc-200 font-mono">{call.caller_phone || '—'}</p>
                        <p className="text-xs text-slate-400 dark:text-zinc-600">{[call.caller_city, call.caller_country].filter(Boolean).join(', ') || '—'}</p>
                      </td>
                      <td className="py-3.5 px-5">
                        <div className="flex flex-col gap-1">
                          {call.spam_label ? (
                            <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold w-fit ${isSpam ? 'bg-red-100 text-red-700 dark:bg-red-500/15 dark:text-red-400' : 'bg-emerald-100 text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-400'}`}>
                              {isSpam ? <PhoneOff className="w-3 h-3" /> : <Phone className="w-3 h-3" />}
                              {isSpam ? 'Spam' : 'Real'}{call.scam_probability != null ? ` · ${call.scam_probability}%` : ''}
                            </span>
                          ) : <span className="text-xs text-slate-300 dark:text-zinc-700">—</span>}
                          {call.urgency_level && (
                            <span className={`px-2 py-0.5 rounded-full text-xs font-semibold w-fit ${URGENCY_BADGE[call.urgency_level] ?? 'bg-slate-100 text-slate-500 dark:bg-zinc-800 dark:text-zinc-500'}`}>
                              {call.urgency_level.charAt(0).toUpperCase() + call.urgency_level.slice(1)}
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="py-3.5 px-5">
                        {call.dispatch_types.length > 0 ? (
                          <div className="flex gap-1.5">
                            {call.dispatch_types.map(t => (
                              <span key={t} className="flex items-center" title={t}>{DISPATCH_ICON[t]}</span>
                            ))}
                          </div>
                        ) : <span className="text-xs text-slate-300 dark:text-zinc-700">—</span>}
                      </td>
                      <td className="py-3.5 px-5">
                        <span className={`px-2.5 py-1 rounded-full text-xs font-semibold ${STATUS_BADGE[call.status ?? ''] ?? 'bg-slate-100 text-slate-500 dark:bg-zinc-800 dark:text-zinc-500'}`}>
                          {call.status || '—'}
                        </span>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </Layout>
  )
}
