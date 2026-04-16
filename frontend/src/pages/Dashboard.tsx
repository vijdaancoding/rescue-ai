import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import Layout from '../components/Layout'
import { Phone, PhoneOff, Activity, Clock, Wifi, MapPin, TrendingUp, CheckCircle, ShieldAlert, Zap } from 'lucide-react'

const API_WS_URL = (import.meta.env.VITE_API_URL || 'http://localhost:8000')
  .replace(/^http/, 'ws')

interface AnalysisSummary {
  spam_score: number
  spam_label: string
  urgency_score: number
  urgency_label: string
  analysis_count: number
}

const URGENCY_BADGE: Record<string, string> = {
  critical: 'bg-red-100 text-red-700 border-red-300',
  high: 'bg-orange-100 text-orange-700 border-orange-300',
  medium: 'bg-yellow-100 text-yellow-700 border-yellow-300',
  low: 'bg-green-100 text-green-700 border-green-300',
}

export default function Dashboard() {
  const navigate = useNavigate()
  // Latest analysis result received from any active call
  const [latestAnalysis, setLatestAnalysis] = useState<AnalysisSummary | null>(null)
  const dashboardWsRef = useRef<WebSocket | null>(null)

  // Connect to /ws/dashboard for live analysis push
  useEffect(() => {
    let isCleanup = false
    const ws = new WebSocket(`${API_WS_URL}/ws/dashboard`)
    dashboardWsRef.current = ws

    ws.onmessage = (event) => {
      if (isCleanup) return
      try {
        const data = JSON.parse(event.data)
        if (data.type === 'analysis_update') {
          setLatestAnalysis({
            spam_score: data.spam_score,
            spam_label: data.spam_label,
            urgency_score: data.urgency_score,
            urgency_label: data.urgency_label,
            analysis_count: data.analysis_count,
          })
        }
      } catch {
        // ignore malformed frames
      }
    }

    return () => {
      isCleanup = true
      ws.close()
    }
  }, [])

  const waitingCalls = [
    { id: 1, type: 'incoming', status: 'Ringing', label: 'Incoming Call...', time: 'Just now' },
    { id: 2, type: 'blocked', status: 'Staged-out', label: 'Blocked Prank Call 1', time: '2 min ago' },
    { id: 3, type: 'blocked', status: 'Staged-out', label: 'Blocked Prank Call 2', time: '5 min ago' },
    { id: 4, type: 'blocked', status: 'Staged-out', label: 'Blocked Prank Call 3', time: '8 min ago' },
  ]

  const stats = [
    { label: 'Active Units', value: '14', trend: '+2', icon: Activity, color: 'teal', bgColor: 'bg-teal-500' },
    { label: 'System Latency', value: '12ms', trend: '-3ms', icon: Clock, color: 'green', bgColor: 'bg-green-500' },
    { label: 'Response Rate', value: '98%', trend: '+5%', icon: TrendingUp, color: 'blue', bgColor: 'bg-blue-500' },
  ]

  const isSpam = latestAnalysis?.spam_label === 'spam'
  const urgencyLabel = latestAnalysis?.urgency_label ?? 'medium'

  return (
    <Layout title="Live View">
      <div className="space-y-6">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {stats.map((stat, index) => {
            const Icon = stat.icon
            return (
              <div
                key={index}
                className="card card-hover bg-gradient-to-br from-white to-gray-50"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600 mb-1">{stat.label}</p>
                    <p className="text-3xl font-bold text-gray-900 mb-2">{stat.value}</p>
                    <div className="flex items-center gap-1 text-sm">
                      <TrendingUp className="w-4 h-4 text-green-600" />
                      <span className="text-green-600 font-medium">{stat.trend}</span>
                    </div>
                  </div>
                  <div className={`w-16 h-16 ${stat.bgColor} rounded-2xl flex items-center justify-center shadow-lg`}>
                    <Icon className="w-8 h-8 text-white" />
                  </div>
                </div>
              </div>
            )
          })}
        </div>

        {/* Live AI Analysis Banner — shown when a call is active */}
        {latestAnalysis && (
          <div className={`card border-2 transition-all duration-500 ${isSpam ? 'border-red-300 bg-red-50' : 'border-teal-200 bg-teal-50'}`}>
            <div className="flex items-center justify-between flex-wrap gap-4">
              <div>
                <h2 className="text-lg font-bold text-gray-900 mb-1">Live AI Call Analysis</h2>
                <p className="text-sm text-gray-500">
                  Updated {latestAnalysis.analysis_count} time{latestAnalysis.analysis_count !== 1 ? 's' : ''} this call
                </p>
              </div>
              <div className="flex items-center gap-3 flex-wrap">
                {/* Spam indicator */}
                <div className={`flex items-center gap-2 px-4 py-2 rounded-xl border-2 font-semibold text-sm ${isSpam ? 'bg-red-100 border-red-300 text-red-700' : 'bg-green-100 border-green-300 text-green-700'}`}>
                  <ShieldAlert className="w-4 h-4" />
                  Spam: {Math.round(latestAnalysis.spam_score * 100)}%
                  <span className={`ml-1 px-2 py-0.5 rounded-full text-xs font-bold ${isSpam ? 'bg-red-200' : 'bg-green-200'}`}>
                    {latestAnalysis.spam_label === 'spam' ? 'SPAM' : 'REAL'}
                  </span>
                </div>
                {/* Urgency indicator */}
                <div className={`flex items-center gap-2 px-4 py-2 rounded-xl border-2 font-semibold text-sm ${URGENCY_BADGE[urgencyLabel] ?? 'bg-gray-100 border-gray-200 text-gray-700'}`}>
                  <Zap className="w-4 h-4" />
                  Urgency: {Math.round(latestAnalysis.urgency_score * 100)}%
                  <span className="ml-1 px-2 py-0.5 rounded-full text-xs font-bold bg-white/60">
                    {urgencyLabel.toUpperCase()}
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Left Column */}
          <div className="space-y-6">
            {/* Waiting Calls */}
            <div className="card">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-bold text-gray-900">Waiting Calls</h2>
                <span className="badge badge-info">
                  {waitingCalls.filter(c => c.type === 'incoming').length} Active
                </span>
              </div>
              <div className="space-y-3">
                {waitingCalls.map((call) => (
                  <div
                    key={call.id}
                    onClick={() => call.type === 'incoming' && navigate('/live')}
                    className={`flex items-center gap-4 p-4 rounded-xl border-2 transition-all duration-300 ${
                      call.type === 'incoming'
                        ? 'bg-gradient-to-r from-red-50 to-orange-50 border-red-300 cursor-pointer hover:shadow-lg hover:scale-102 animate-pulse-slow'
                        : 'bg-gray-50 border-gray-200 hover:bg-gray-100'
                    }`}
                  >
                    <div
                      className={`w-14 h-14 rounded-xl flex items-center justify-center shadow-md ${
                        call.type === 'incoming'
                          ? 'bg-gradient-to-br from-red-500 to-red-600'
                          : 'bg-gradient-to-br from-gray-400 to-gray-500'
                      }`}
                    >
                      {call.type === 'incoming' ? (
                        <Phone className="w-7 h-7 text-white animate-pulse" />
                      ) : (
                        <PhoneOff className="w-7 h-7 text-white" />
                      )}
                    </div>
                    <div className="flex-1">
                      <p className="font-bold text-gray-900">{call.label}</p>
                      <p className="text-sm text-gray-600">{call.status}</p>
                      <p className="text-xs text-gray-500 mt-1">{call.time}</p>
                    </div>
                    {/* Show live analysis badges on the active incoming call */}
                    {call.type === 'incoming' && latestAnalysis ? (
                      <div className="flex flex-col gap-1 items-end">
                        <span className={`text-xs px-2 py-0.5 rounded-full font-semibold border ${isSpam ? 'bg-red-100 border-red-300 text-red-700' : 'bg-green-100 border-green-300 text-green-700'}`}>
                          {isSpam ? 'SPAM' : 'REAL'}
                        </span>
                        <span className={`text-xs px-2 py-0.5 rounded-full font-semibold border ${URGENCY_BADGE[urgencyLabel] ?? 'bg-gray-100 border-gray-200'}`}>
                          {urgencyLabel.toUpperCase()}
                        </span>
                      </div>
                    ) : call.type === 'incoming' ? (
                      <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse" />
                    ) : null}
                  </div>
                ))}
              </div>
            </div>

            {/* System Status */}
            <div className="card bg-gradient-to-br from-gray-900 to-gray-800 text-white">
              <h2 className="text-xl font-bold mb-6">System Status</h2>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <CheckCircle className="w-5 h-5 text-green-400" />
                    <span>Network Connection</span>
                  </div>
                  <span className="badge bg-green-500 text-white">Stable</span>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <CheckCircle className="w-5 h-5 text-green-400" />
                    <span>Database Connection</span>
                  </div>
                  <span className="badge bg-green-500 text-white">Active</span>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <Wifi className="w-5 h-5 text-blue-400" />
                    <span>WebSocket Connection</span>
                  </div>
                  <span className="badge bg-blue-500 text-white">Connected</span>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <Activity className="w-5 h-5 text-teal-400" />
                    <span>AI Analysis Pipeline</span>
                  </div>
                  <span className={`badge ${latestAnalysis ? 'bg-teal-500' : 'bg-gray-500'} text-white`}>
                    {latestAnalysis ? 'Active' : 'Standby'}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Right Column - Map */}
          <div className="card card-hover h-[600px] flex flex-col">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold text-gray-900">Live Map</h2>
              <button className="btn btn-secondary text-sm py-2">
                Full Screen
              </button>
            </div>
            <div className="flex items-center justify-center flex-1 bg-gradient-to-br from-blue-50 to-teal-50 rounded-xl relative overflow-hidden border-2 border-gray-200">
              {/* Map Placeholder */}
              <div className="absolute inset-0 bg-gradient-to-br from-gray-100 via-gray-200 to-gray-300">
                <div className="absolute inset-0" style={{
                  backgroundImage: `
                    linear-gradient(to right, rgba(20,184,166,0.1) 1px, transparent 1px),
                    linear-gradient(to bottom, rgba(20,184,166,0.1) 1px, transparent 1px)
                  `,
                  backgroundSize: '40px 40px'
                }} />

                <div className="absolute top-1/4 left-1/3 group">
                  <div className="w-6 h-6 bg-red-500 rounded-full animate-pulse shadow-2xl border-4 border-white" />
                  <div className="absolute inset-0 w-6 h-6 bg-red-500 rounded-full animate-ping opacity-75" />
                </div>
                <div className="absolute top-1/2 left-1/2">
                  <div className="w-6 h-6 bg-blue-500 rounded-full shadow-2xl border-4 border-white" />
                </div>
                <div className="absolute bottom-1/3 right-1/3">
                  <div className="w-6 h-6 bg-green-500 rounded-full shadow-2xl border-4 border-white" />
                </div>
                <div className="absolute top-2/3 left-1/4">
                  <div className="w-6 h-6 bg-yellow-500 rounded-full shadow-2xl border-4 border-white" />
                </div>
                <div className="absolute bottom-1/4 right-1/4">
                  <div className="w-6 h-6 bg-purple-500 rounded-full shadow-2xl border-4 border-white" />
                </div>
              </div>

              <div className="absolute bottom-4 left-1/2 -translate-x-1/2 glass px-6 py-3 rounded-xl shadow-2xl flex items-center gap-3">
                <MapPin className="w-5 h-5 text-teal-600" />
                <div>
                  <p className="text-sm font-bold text-gray-900">Live Tracking</p>
                  <p className="text-xs text-gray-600">5 units dispatched</p>
                </div>
              </div>

              <div className="absolute top-4 right-4 glass px-4 py-3 rounded-xl shadow-lg">
                <p className="text-xs font-bold text-gray-700 mb-2">Legend</p>
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 bg-red-500 rounded-full" />
                    <span className="text-xs text-gray-600">Emergency</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 bg-blue-500 rounded-full" />
                    <span className="text-xs text-gray-600">En Route</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 bg-green-500 rounded-full" />
                    <span className="text-xs text-gray-600">Available</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  )
}
