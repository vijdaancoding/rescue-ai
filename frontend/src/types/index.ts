// Type definitions for the application

export interface User {
  id: string
  name: string
  operatorId: string
  email: string
}

export interface Call {
  id: number
  type: 'incoming' | 'blocked' | 'emergency'
  status: string
  label: string
  time?: string
  date?: string
  duration?: string
  operatorId?: string
  priority?: 'High' | 'Medium' | 'Low'
  location?: string
}

export interface SystemHealth {
  activeUnits: number
  systemLatency: string
  responseRate: string
}

export interface Stat {
  label: string
  value: string
  trend: string
  icon: any
  color: string
  bgColor: string
}

export interface NavItem {
  icon: any
  label: string
  path: string
}

export interface ToastProps {
  message: string
  type: 'success' | 'error' | 'info'
  onClose: () => void
  duration?: number
}

export interface AuthContextType {
  user: User | null
  token: string | null
  login: (operatorId: string, password: string) => void
  logout: () => void
  isAuthenticated: boolean
}

// ── API response types ─────────────────────────────────────────────────────────

export interface CallSummary {
  id: string
  start_time: string | null
  end_time: string | null
  duration_seconds: number | null
  status: string | null
  caller_phone: string | null
  caller_city: string | null
  caller_country: string | null
  spam_label: string | null       // "spam" | "not_spam" | null
  urgency_level: string | null    // "critical" | "high" | "medium" | "low" | null
  scam_probability: number | null // 0–100
  dispatch_types: string[]        // ["ambulance", "police", ...]
}

export interface DispatchRecord {
  id: string
  created_at: string
  call_id: string
  dispatch_type: string   // police | ambulance | firefighters
  status: string          // dispatched | en_route | on_scene | resolved
  notes: string | null
  ai_recommended: boolean
}

export interface AnalysisData {
  spam_score: number
  spam_label: string
  onnx_spam_score: number
  gemini_spam_score: number
  urgency_score: number
  urgency_label: string
  reasoning: string
  dispatch_recommendation: string[]
  analysis_count: number
  transcript_word_count: number
}

export interface AnalyticsSummary {
  total_calls: number
  real_calls: number
  spam_calls: number
  dispatched: number
  false_alarms: number
  active: number
  avg_processing_latency_ms: number
  urgency_breakdown: Record<string, number>
}

export interface AnalyticsByDay {
  date: string
  total: number
  spam: number
  real: number
}

export interface AnalyticsDispatch {
  dispatch_type: string
  count: number
}
