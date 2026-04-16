import { useState, useEffect, useCallback } from 'react'
import Layout from '../components/Layout'
import { Phone, PhoneOff, Clock, Calendar, Filter, Download, Search, Shield, HeartPulse, Flame, Loader2 } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import type { CallSummary } from '../types'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const URGENCY_BADGE: Record<string, string> = {
  critical: 'bg-red-100 text-red-700',
  high: 'bg-orange-100 text-orange-700',
  medium: 'bg-yellow-100 text-yellow-700',
  low: 'bg-green-100 text-green-700',
}

const STATUS_BADGE: Record<string, string> = {
  Dispatched: 'bg-blue-100 text-blue-700',
  FalseAlarm: 'bg-gray-100 text-gray-600',
  Active: 'bg-green-100 text-green-700',
  Incoming: 'bg-yellow-100 text-yellow-700',
}

const DISPATCH_ICON: Record<string, React.ReactNode> = {
  police: <Shield className="w-3.5 h-3.5 text-blue-600" title="Police" />,
  ambulance: <HeartPulse className="w-3.5 h-3.5 text-red-600" title="Ambulance" />,
  firefighters: <Flame className="w-3.5 h-3.5 text-orange-600" title="Firefighters" />,
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

  // Filter state
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
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [token, statusFilter, spamFilter, dateFrom, dateTo, search])

  useEffect(() => {
    const id = setTimeout(fetchCalls, 300) // debounce search
    return () => clearTimeout(id)
  }, [fetchCalls])

  // Aggregate stats from current result set
  const totalCalls = calls.length
  const realCalls = calls.filter(c => c.spam_label === 'not_spam').length
  const spamCalls = calls.filter(c => c.spam_label === 'spam').length
  const dispatched = calls.filter(c => c.status === 'Dispatched').length

  return (
    <Layout title="Call History">
      <div className="space-y-6">

        {/* Header */}
        <div className="card">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <h2 className="text-2xl font-bold text-gray-900 mb-1">Call History Log</h2>
              <p className="text-gray-500 text-sm">Complete record of all emergency calls from Supabase</p>
            </div>
            <button className="btn btn-primary flex items-center gap-2 self-start">
              <Download className="w-4 h-4" />
              Export
            </button>
          </div>
        </div>

        {/* Filters */}
        <div className="card">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
            {/* Search */}
            <div className="relative lg:col-span-2">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search phone or city..."
                value={search}
                onChange={e => setSearch(e.target.value)}
                className="w-full pl-9 pr-4 py-2.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
              />
            </div>

            {/* Status filter */}
            <div className="relative">
              <Filter className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <select
                value={statusFilter}
                onChange={e => setStatusFilter(e.target.value)}
                className="w-full pl-9 pr-4 py-2.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 appearance-none bg-white"
              >
                <option value="">All Statuses</option>
                <option value="Active">Active</option>
                <option value="Dispatched">Dispatched</option>
                <option value="FalseAlarm">False Alarm</option>
                <option value="Incoming">Incoming</option>
              </select>
            </div>

            {/* Spam filter */}
            <div className="relative">
              <Shield className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <select
                value={spamFilter}
                onChange={e => setSpamFilter(e.target.value)}
                className="w-full pl-9 pr-4 py-2.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 appearance-none bg-white"
              >
                <option value="">All Types</option>
                <option value="not_spam">Real Emergencies</option>
                <option value="spam">Prank / Spam</option>
              </select>
            </div>

            {/* Date range */}
            <div className="flex gap-2 items-center">
              <input
                type="date"
                value={dateFrom}
                onChange={e => setDateFrom(e.target.value)}
                className="flex-1 px-2 py-2.5 border border-gray-300 rounded-lg text-xs focus:outline-none focus:ring-2 focus:ring-teal-500"
              />
              <span className="text-gray-400 text-xs">–</span>
              <input
                type="date"
                value={dateTo}
                onChange={e => setDateTo(e.target.value)}
                className="flex-1 px-2 py-2.5 border border-gray-300 rounded-lg text-xs focus:outline-none focus:ring-2 focus:ring-teal-500"
              />
            </div>
          </div>
        </div>

        {/* Table */}
        <div className="card overflow-x-auto">
          {loading ? (
            <div className="flex items-center justify-center py-16 gap-3 text-gray-400">
              <Loader2 className="w-5 h-5 animate-spin" />
              <span className="text-sm">Loading calls...</span>
            </div>
          ) : error ? (
            <div className="text-center py-12">
              <p className="text-red-600 text-sm font-medium">{error}</p>
            </div>
          ) : calls.length === 0 ? (
            <div className="text-center py-12">
              <Phone className="w-12 h-12 text-gray-300 mx-auto mb-3" />
              <p className="text-gray-500 text-sm">No calls match your filters</p>
            </div>
          ) : (
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-100">
                  <th className="text-left py-3 px-4 text-xs font-semibold text-gray-500 uppercase tracking-wide">Date & Time</th>
                  <th className="text-left py-3 px-4 text-xs font-semibold text-gray-500 uppercase tracking-wide">Duration</th>
                  <th className="text-left py-3 px-4 text-xs font-semibold text-gray-500 uppercase tracking-wide">Phone / Location</th>
                  <th className="text-left py-3 px-4 text-xs font-semibold text-gray-500 uppercase tracking-wide">AI Signal</th>
                  <th className="text-left py-3 px-4 text-xs font-semibold text-gray-500 uppercase tracking-wide">Dispatched</th>
                  <th className="text-left py-3 px-4 text-xs font-semibold text-gray-500 uppercase tracking-wide">Status</th>
                </tr>
              </thead>
              <tbody>
                {calls.map(call => {
                  const { date, time } = formatDateTime(call.start_time)
                  const isSpam = call.spam_label === 'spam'
                  return (
                    <tr key={call.id} className="border-b border-gray-50 hover:bg-gray-50 transition-colors">
                      <td className="py-3.5 px-4">
                        <div className="flex items-center gap-2">
                          <Calendar className="w-4 h-4 text-gray-300 flex-shrink-0" />
                          <div>
                            <p className="text-sm font-medium text-gray-900">{date}</p>
                            <p className="text-xs text-gray-400">{time}</p>
                          </div>
                        </div>
                      </td>
                      <td className="py-3.5 px-4">
                        <div className="flex items-center gap-1.5 text-sm text-gray-600">
                          <Clock className="w-3.5 h-3.5 text-gray-300" />
                          {formatDuration(call.duration_seconds)}
                        </div>
                      </td>
                      <td className="py-3.5 px-4">
                        <p className="text-sm text-gray-800 font-mono">{call.caller_phone || '—'}</p>
                        <p className="text-xs text-gray-400">{[call.caller_city, call.caller_country].filter(Boolean).join(', ') || '—'}</p>
                      </td>
                      <td className="py-3.5 px-4">
                        <div className="flex flex-col gap-1">
                          {call.spam_label ? (
                            <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold w-fit ${isSpam ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'}`}>
                              {isSpam ? <PhoneOff className="w-3 h-3" /> : <Phone className="w-3 h-3" />}
                              {isSpam ? 'Spam' : 'Real'} {call.scam_probability != null ? `· ${call.scam_probability}%` : ''}
                            </span>
                          ) : <span className="text-xs text-gray-300">No analysis</span>}
                          {call.urgency_level && (
                            <span className={`px-2 py-0.5 rounded-full text-xs font-semibold w-fit ${URGENCY_BADGE[call.urgency_level] ?? 'bg-gray-100 text-gray-500'}`}>
                              {call.urgency_level.charAt(0).toUpperCase() + call.urgency_level.slice(1)}
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="py-3.5 px-4">
                        {call.dispatch_types.length > 0 ? (
                          <div className="flex gap-1">
                            {call.dispatch_types.map(t => (
                              <span key={t} className="flex items-center gap-0.5" title={t}>
                                {DISPATCH_ICON[t]}
                              </span>
                            ))}
                          </div>
                        ) : (
                          <span className="text-xs text-gray-300">—</span>
                        )}
                      </td>
                      <td className="py-3.5 px-4">
                        <span className={`px-2.5 py-1 rounded-full text-xs font-semibold ${STATUS_BADGE[call.status ?? ''] ?? 'bg-gray-100 text-gray-500'}`}>
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

        {/* Stats */}
        {!loading && !error && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="card text-center py-4">
              <p className="text-3xl font-bold text-gray-900">{totalCalls}</p>
              <p className="text-xs text-gray-500 mt-1">Total Calls</p>
            </div>
            <div className="card text-center py-4">
              <p className="text-3xl font-bold text-green-600">{realCalls}</p>
              <p className="text-xs text-gray-500 mt-1">Real Emergencies</p>
            </div>
            <div className="card text-center py-4">
              <p className="text-3xl font-bold text-red-600">{spamCalls}</p>
              <p className="text-xs text-gray-500 mt-1">Prank / Spam</p>
            </div>
            <div className="card text-center py-4">
              <p className="text-3xl font-bold text-blue-600">{dispatched}</p>
              <p className="text-xs text-gray-500 mt-1">Dispatched</p>
            </div>
          </div>
        )}
      </div>
    </Layout>
  )
}
