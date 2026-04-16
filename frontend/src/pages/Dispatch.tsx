import { useState, useEffect } from 'react'
import { useParams, useNavigate, useLocation } from 'react-router-dom'
import Layout from '../components/Layout'
import { Shield, HeartPulse, Flame, CheckCircle, AlertTriangle, ArrowLeft, Siren } from 'lucide-react'
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
  iconBg: string
}

const SERVICES: ServiceCard[] = [
  {
    type: 'police',
    label: 'Police',
    description: 'Crime, violence, security threat',
    icon: <Shield className="w-8 h-8" />,
    selectedBg: 'bg-blue-50',
    selectedBorder: 'border-blue-500',
    selectedText: 'text-blue-700',
    iconBg: 'bg-blue-100 text-blue-600',
  },
  {
    type: 'ambulance',
    label: 'Ambulance',
    description: 'Medical emergency, injuries',
    icon: <HeartPulse className="w-8 h-8" />,
    selectedBg: 'bg-red-50',
    selectedBorder: 'border-red-500',
    selectedText: 'text-red-700',
    iconBg: 'bg-red-100 text-red-600',
  },
  {
    type: 'firefighters',
    label: 'Firefighters',
    description: 'Fire, explosion, smoke, entrapment',
    icon: <Flame className="w-8 h-8" />,
    selectedBg: 'bg-orange-50',
    selectedBorder: 'border-orange-500',
    selectedText: 'text-orange-700',
    iconBg: 'bg-orange-100 text-orange-600',
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

  // Pre-select AI recommendations
  useEffect(() => {
    if (analysis?.dispatch_recommendation?.length) {
      setSelected(new Set(analysis.dispatch_recommendation))
    }
  }, [analysis])

  // Fetch existing dispatches for this call
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
    } catch (e: any) {
      setError(e.message)
    } finally {
      setSubmitting(false)
    }
  }

  const handleFalseAlarm = async () => {
    if (!callId || !token) return
    await fetch(`${API_URL}/calls/${callId}/status`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ status: 'FalseAlarm' }),
    }).catch(() => {})
    navigate('/dashboard')
  }

  const pendingSelection = [...selected].filter(t => !alreadyDispatched.has(t))

  return (
    <Layout title="Dispatch Unit">
      <div className="max-w-2xl mx-auto space-y-6">

        {/* Back */}
        <button
          onClick={() => navigate('/live')}
          className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-800 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Live Call
        </button>

        {/* Header */}
        <div className="card">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 bg-red-100 rounded-xl flex items-center justify-center">
              <Siren className="w-7 h-7 text-red-600" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Dispatch Emergency Services</h1>
              <p className="text-sm text-gray-500">Call ID: <span className="font-mono text-xs">{callId}</span></p>
            </div>
          </div>
        </div>

        {/* AI Recommendation Banner */}
        {analysis && analysis.dispatch_recommendation.length > 0 && (
          <div className="card bg-teal-50 border-2 border-teal-200">
            <div className="flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-teal-600 mt-0.5 flex-shrink-0" />
              <div>
                <p className="font-semibold text-teal-800 text-sm">AI Recommendation</p>
                <p className="text-teal-700 text-sm mt-0.5">{analysis.reasoning}</p>
                <div className="flex flex-wrap gap-2 mt-2">
                  {analysis.dispatch_recommendation.map(type => (
                    <span key={type} className="px-2.5 py-0.5 bg-teal-100 border border-teal-300 text-teal-800 rounded-full text-xs font-bold uppercase">
                      {type}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Already dispatched notice */}
        {existingDispatches.length > 0 && (
          <div className="card bg-green-50 border border-green-200">
            <p className="text-sm font-semibold text-green-800 mb-2">Already Dispatched</p>
            <div className="flex flex-wrap gap-2">
              {existingDispatches.map(d => (
                <span key={d.id} className="flex items-center gap-1.5 px-3 py-1 bg-green-100 border border-green-300 text-green-700 rounded-full text-xs font-semibold">
                  <CheckCircle className="w-3.5 h-3.5" />
                  {d.dispatch_type.charAt(0).toUpperCase() + d.dispatch_type.slice(1)} — {d.status}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Service Selection */}
        <div className="space-y-3">
          {SERVICES.map(svc => {
            const isAlreadyDispatched = alreadyDispatched.has(svc.type)
            const isSelected = selected.has(svc.type)
            const isAiRec = analysis?.dispatch_recommendation?.includes(svc.type)

            return (
              <button
                key={svc.type}
                onClick={() => toggleService(svc.type)}
                disabled={isAlreadyDispatched}
                className={`w-full flex items-center gap-4 p-5 rounded-2xl border-2 text-left transition-all duration-200 ${
                  isAlreadyDispatched
                    ? 'bg-gray-50 border-gray-200 opacity-60 cursor-not-allowed'
                    : isSelected
                    ? `${svc.selectedBg} ${svc.selectedBorder} shadow-md`
                    : 'bg-white border-gray-200 hover:border-gray-300 hover:shadow-sm'
                }`}
              >
                <div className={`w-14 h-14 rounded-xl flex items-center justify-center flex-shrink-0 ${
                  isAlreadyDispatched ? 'bg-gray-100 text-gray-400' : svc.iconBg
                }`}>
                  {isAlreadyDispatched ? <CheckCircle className="w-8 h-8 text-green-500" /> : svc.icon}
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <p className={`text-lg font-bold ${isSelected && !isAlreadyDispatched ? svc.selectedText : 'text-gray-800'}`}>
                      {svc.label}
                    </p>
                    {isAiRec && !isAlreadyDispatched && (
                      <span className="px-2 py-0.5 bg-teal-100 border border-teal-300 text-teal-700 rounded-full text-xs font-semibold">
                        AI Recommended
                      </span>
                    )}
                    {isAlreadyDispatched && (
                      <span className="px-2 py-0.5 bg-green-100 border border-green-300 text-green-700 rounded-full text-xs font-semibold">
                        Dispatched
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-gray-500">{svc.description}</p>
                </div>
                {isSelected && !isAlreadyDispatched && (
                  <CheckCircle className={`w-6 h-6 flex-shrink-0 ${svc.selectedText}`} />
                )}
              </button>
            )
          })}
        </div>

        {/* Notes */}
        <div className="card">
          <label className="block text-sm font-semibold text-gray-700 mb-2">Notes (optional)</label>
          <textarea
            value={notes}
            onChange={e => setNotes(e.target.value)}
            placeholder="Add any additional context for the dispatch..."
            className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent resize-none text-sm"
            rows={3}
          />
        </div>

        {/* Error */}
        {error && (
          <div className="card bg-red-50 border border-red-200">
            <p className="text-sm text-red-700 font-medium">{error}</p>
          </div>
        )}

        {/* Success */}
        {done && (
          <div className="card bg-green-50 border border-green-200 flex items-center gap-3">
            <CheckCircle className="w-5 h-5 text-green-600" />
            <p className="text-sm text-green-700 font-semibold">Units dispatched! Returning to call...</p>
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-3">
          <button
            onClick={handleDeploy}
            disabled={pendingSelection.length === 0 || submitting || done}
            className="flex-1 btn bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 text-white border-0 py-3 text-base font-bold disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {submitting ? 'Deploying...' : `Deploy ${pendingSelection.length > 0 ? `(${pendingSelection.length})` : ''} Selected`}
          </button>
          <button
            onClick={handleFalseAlarm}
            disabled={submitting}
            className="btn bg-yellow-400 hover:bg-yellow-500 text-white border-0 py-3 px-5 font-semibold disabled:opacity-50"
          >
            False Alarm
          </button>
        </div>
      </div>
    </Layout>
  )
}
