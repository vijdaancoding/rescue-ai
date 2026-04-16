import { useState, useEffect } from 'react'
import { useParams, useNavigate, useLocation } from 'react-router-dom'
import Layout from '../components/Layout'
import { Shield, HeartPulse, Flame, CheckCircle, AlertTriangle, ArrowLeft, Siren, Bell } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import type { AnalysisData, DispatchRecord } from '../types'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

interface ServiceCard {
  type: 'police' | 'ambulance' | 'firefighters'
  label: string
  description: string
  icon: React.ReactNode
  selectedBg: string
  selectedBorder: string
  selectedText: string
}

const SERVICES: ServiceCard[] = [
  {
    type: 'police',
    label: 'Police',
    description: 'Crime, violence, security threat',
    icon: <Shield className="w-6 h-6" />,
    selectedBg: 'bg-blue-50 dark:bg-blue-500/10',
    selectedBorder: 'border-blue-400 dark:border-blue-500/50',
    selectedText: 'text-blue-700 dark:text-blue-400',
  },
  {
    type: 'ambulance',
    label: 'Ambulance',
    description: 'Medical emergency, injuries',
    icon: <HeartPulse className="w-6 h-6" />,
    selectedBg: 'bg-red-50 dark:bg-red-500/10',
    selectedBorder: 'border-red-400 dark:border-red-500/50',
    selectedText: 'text-red-700 dark:text-red-400',
  },
  {
    type: 'firefighters',
    label: 'Firefighters',
    description: 'Fire, explosion, smoke, entrapment',
    icon: <Flame className="w-6 h-6" />,
    selectedBg: 'bg-orange-50 dark:bg-orange-500/10',
    selectedBorder: 'border-orange-400 dark:border-orange-500/50',
    selectedText: 'text-orange-700 dark:text-orange-400',
  },
]

export default function Dispatch() {
  const { callId } = useParams<{ callId: string }>()
  const navigate = useNavigate()
  const location = useLocation()
  const { token } = useAuth()

  const analysis = location.state?.analysis as AnalysisData | undefined

  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [existingDispatches, setExistingDispatches] = useState<DispatchRecord[]>([])
  const [notes, setNotes] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [done, setDone] = useState(false)

  useEffect(() => {
    if (analysis?.dispatch_recommendation?.length) {
      setSelected(new Set(analysis.dispatch_recommendation))
    }
  }, [analysis])

  useEffect(() => {
    if (!callId || !token) return
    fetch(`${API_URL}/api/dispatches/${callId}`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(r => r.ok ? r.json() : [])
      .then((data: DispatchRecord[]) => setExistingDispatches(data))
      .catch(() => {})
  }, [callId, token])

  const alreadyDispatched = new Set(existingDispatches.map(d => d.dispatch_type))

  const toggleService = (type: string) => {
    if (alreadyDispatched.has(type)) return
    setSelected(prev => {
      const next = new Set(prev)
      next.has(type) ? next.delete(type) : next.add(type)
      return next
    })
  }

  const handleDeploy = async () => {
    if (!callId || !token || selected.size === 0) return
    setSubmitting(true)
    setError(null)
    try {
      const res = await fetch(`${API_URL}/api/dispatches/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          call_id: callId,
          dispatch_types: [...selected],
          ai_recommended: analysis?.dispatch_recommendation ?? [],
          notes: notes || null,
        }),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail || 'Dispatch failed')
      }
      setDone(true)
      setTimeout(() => navigate('/live'), 1500)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Unknown error')
    } finally {
      setSubmitting(false)
    }
  }

  const handleFalseAlarm = async () => {
    if (!callId || !token) return
    await fetch(`${API_URL}/calls/${callId}/status`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
      body: JSON.stringify({ status: 'FalseAlarm' }),
    }).catch(() => {})
    navigate('/dashboard')
  }

  const pendingSelection = [...selected].filter(t => !alreadyDispatched.has(t))

  return (
    <Layout title="Dispatch Unit">
      <div className="max-w-xl mx-auto space-y-4">

        <button
          onClick={() => navigate('/live')}
          className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-700 dark:text-zinc-500 dark:hover:text-zinc-300 transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          Back to Live Call
        </button>

        {/* Header */}
        <div className="card">
          <div className="flex items-center gap-4">
            <div className="w-11 h-11 bg-red-50 border border-red-200 dark:bg-red-500/15 dark:border-red-500/25 rounded-xl flex items-center justify-center flex-shrink-0">
              <Siren className="w-5 h-5 text-red-600 dark:text-red-400" />
            </div>
            <div>
              <h1 className="text-lg font-semibold text-slate-900 dark:text-zinc-100">Dispatch Emergency Services</h1>
              <p className="text-xs text-slate-400 dark:text-zinc-500 mt-0.5 font-mono">
                Call: <span className="text-slate-600 dark:text-zinc-400">{callId}</span>
              </p>
            </div>
          </div>
        </div>

        {/* AI Recommendation */}
        {analysis && analysis.dispatch_recommendation.length > 0 && (
          <div className="card bg-teal-50 border-teal-200 dark:bg-cyan-500/5 dark:border-cyan-500/20">
            <div className="flex items-start gap-3">
              <AlertTriangle className="w-4 h-4 text-teal-600 dark:text-cyan-400 mt-0.5 flex-shrink-0" />
              <div>
                <p className="text-xs font-semibold text-teal-700 dark:text-cyan-400 uppercase tracking-wider mb-1">AI Recommendation</p>
                <p className="text-sm text-teal-700 dark:text-zinc-400">{analysis.reasoning}</p>
                <div className="flex flex-wrap gap-1.5 mt-2">
                  {analysis.dispatch_recommendation.map(type => (
                    <span key={type} className="px-2.5 py-0.5 bg-teal-100 border border-teal-300 text-teal-800 dark:bg-cyan-500/10 dark:border-cyan-500/25 dark:text-cyan-400 rounded-lg text-xs font-semibold uppercase">
                      {type}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Already dispatched */}
        {existingDispatches.length > 0 && (
          <div className="card bg-emerald-50 border-emerald-200 dark:bg-emerald-500/5 dark:border-emerald-500/20">
            <p className="text-xs font-semibold text-emerald-700 dark:text-emerald-400 uppercase tracking-wider mb-2">Already Dispatched</p>
            <div className="flex flex-wrap gap-1.5">
              {existingDispatches.map(d => (
                <span key={d.id} className="flex items-center gap-1.5 px-3 py-1.5 bg-emerald-100 border border-emerald-300 text-emerald-800 dark:bg-emerald-500/10 dark:border-emerald-500/20 dark:text-emerald-400 rounded-lg text-xs font-semibold">
                  <CheckCircle className="w-3 h-3" />
                  {d.dispatch_type.charAt(0).toUpperCase() + d.dispatch_type.slice(1)} — {d.status}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Service Selection */}
        <div className="space-y-2">
          {SERVICES.map(svc => {
            const isAlreadyDispatched = alreadyDispatched.has(svc.type)
            const isSelected = selected.has(svc.type)
            const isAiRec = analysis?.dispatch_recommendation?.includes(svc.type)

            return (
              <button
                key={svc.type}
                onClick={() => toggleService(svc.type)}
                disabled={isAlreadyDispatched}
                className={`w-full flex items-center gap-4 p-4 rounded-xl border-2 text-left transition-all duration-150 ${
                  isAlreadyDispatched
                    ? 'bg-slate-50 border-slate-200 dark:bg-zinc-900/50 dark:border-zinc-800 opacity-50 cursor-not-allowed'
                    : isSelected
                    ? `${svc.selectedBg} ${svc.selectedBorder}`
                    : 'bg-white border-slate-200 hover:border-slate-300 dark:bg-zinc-900 dark:border-zinc-800 dark:hover:border-zinc-700'
                }`}
              >
                <div className={`w-11 h-11 rounded-xl flex items-center justify-center flex-shrink-0 ${
                  isAlreadyDispatched
                    ? 'bg-slate-100 text-slate-400 dark:bg-zinc-800 dark:text-zinc-600'
                    : isSelected
                    ? `${svc.selectedBg} ${svc.selectedText}`
                    : 'bg-slate-100 text-slate-400 dark:bg-zinc-800 dark:text-zinc-500'
                }`}>
                  {isAlreadyDispatched ? <CheckCircle className="w-5 h-5 text-emerald-500" /> : svc.icon}
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <p className={`text-sm font-semibold ${isSelected && !isAlreadyDispatched ? svc.selectedText : 'text-slate-800 dark:text-zinc-200'}`}>
                      {svc.label}
                    </p>
                    {isAiRec && !isAlreadyDispatched && (
                      <span className="px-1.5 py-0.5 bg-teal-50 border border-teal-200 text-teal-700 dark:bg-cyan-500/10 dark:border-cyan-500/25 dark:text-cyan-400 rounded text-[10px] font-semibold">
                        AI REC
                      </span>
                    )}
                    {isAlreadyDispatched && (
                      <span className="px-1.5 py-0.5 bg-emerald-50 border border-emerald-200 text-emerald-700 dark:bg-emerald-500/10 dark:border-emerald-500/20 dark:text-emerald-400 rounded text-[10px] font-semibold">
                        DISPATCHED
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-slate-400 dark:text-zinc-500 mt-0.5">{svc.description}</p>
                </div>
                {isSelected && !isAlreadyDispatched && (
                  <CheckCircle className={`w-4 h-4 flex-shrink-0 ${svc.selectedText}`} />
                )}
              </button>
            )
          })}
        </div>

        {/* Notes */}
        <div>
          <label className="block text-xs font-semibold text-slate-400 dark:text-zinc-500 uppercase tracking-wider mb-2">Notes (optional)</label>
          <textarea
            value={notes}
            onChange={e => setNotes(e.target.value)}
            placeholder="Add any additional context for the dispatch..."
            className="w-full px-4 py-3 rounded-xl resize-none text-sm transition-all duration-200
              bg-white border border-slate-200 text-slate-900 placeholder:text-slate-400
              dark:bg-zinc-800 dark:border-zinc-700 dark:text-zinc-200 dark:placeholder:text-zinc-600
              focus:outline-none focus:ring-1 focus:ring-teal-500 dark:focus:ring-cyan-500"
            rows={3}
          />
        </div>

        {error && (
          <div className="px-4 py-3 bg-red-50 border border-red-200 dark:bg-red-500/10 dark:border-red-500/25 rounded-xl">
            <p className="text-sm text-red-700 dark:text-red-400">{error}</p>
          </div>
        )}

        {done && (
          <div className="flex items-center gap-3 px-4 py-3 bg-emerald-50 border border-emerald-200 dark:bg-emerald-500/10 dark:border-emerald-500/20 rounded-xl">
            <CheckCircle className="w-4 h-4 text-emerald-600 dark:text-emerald-400 flex-shrink-0" />
            <p className="text-sm text-emerald-700 dark:text-emerald-400 font-semibold">Units dispatched! Returning to call...</p>
          </div>
        )}

        <div className="flex gap-3">
          <button
            onClick={handleFalseAlarm}
            disabled={submitting}
            className="flex items-center gap-2 px-5 py-3 rounded-xl text-sm font-medium disabled:opacity-50 transition-all duration-200
              bg-white border border-slate-200 text-slate-500 hover:bg-amber-50 hover:border-amber-300 hover:text-amber-700
              dark:bg-zinc-800 dark:border-zinc-700 dark:text-zinc-400 dark:hover:bg-amber-500/10 dark:hover:border-amber-500/40 dark:hover:text-amber-400"
          >
            <Bell className="w-4 h-4" />
            False Alarm
          </button>
          <button
            onClick={handleDeploy}
            disabled={pendingSelection.length === 0 || submitting || done}
            className="flex-1 flex items-center justify-center gap-2 py-3 bg-red-600 hover:bg-red-500 disabled:opacity-40 disabled:cursor-not-allowed rounded-xl text-white font-semibold text-sm transition-all duration-200 active:scale-[0.99] shadow-lg shadow-red-500/20"
          >
            <Siren className="w-4 h-4" />
            {submitting ? 'Deploying...' : `Deploy${pendingSelection.length > 0 ? ` (${pendingSelection.length})` : ''} Selected`}
          </button>
        </div>
      </div>
    </Layout>
  )
}
