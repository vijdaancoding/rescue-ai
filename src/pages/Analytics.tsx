import Layout from '../components/Layout'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts'
import { TrendingUp, AlertTriangle, CheckCircle, Clock } from 'lucide-react'

export default function Analytics() {
  // Mock data for Real Emergencies vs Prank Calls
  const emergencyData = [
    { month: 'Jan', emergencies: 45, pranks: 32 },
    { month: 'Feb', emergencies: 52, pranks: 28 },
    { month: 'Mar', emergencies: 38, pranks: 35 },
    { month: 'Apr', emergencies: 48, pranks: 30 },
    { month: 'May', emergencies: 55, pranks: 25 },
    { month: 'Jun', emergencies: 42, pranks: 38 },
  ]

  // Mock data for Response Time Improvement
  const responseData = [
    { month: 'Jan', time: 18 },
    { month: 'Feb', time: 16 },
    { month: 'Mar', time: 19 },
    { month: 'Apr', time: 14 },
    { month: 'May', time: 12 },
    { month: 'Jun', time: 15 },
    { month: 'Jul', time: 11 },
  ]

  const recentCalls = [
    { date: '17-02-2025', time: '14:32', level: 'High', status: 'Urgent: Dispatch', color: 'red' },
    { date: '17-02-2025', time: '13:45', level: 'Medium', status: 'Status: Pending', color: 'yellow' },
    { date: '17-02-2025', time: '12:18', level: 'Low', status: 'Status: Dispatched', color: 'blue' },
  ]

  return (
    <Layout title="Post-Incident Report">
      <div className="space-y-6">
        {/* Header Section */}
        <div className="card">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Incident Analytics</h2>
          <p className="text-gray-600 mb-4">
            Comprehensive analysis of incident trends with call patterns
          </p>
          <div className="flex gap-3">
            <button className="btn bg-white text-gray-700 border border-gray-300 hover:bg-gray-50">
              View All Reports
            </button>
            <button className="btn btn-primary">
              Export Report
            </button>
          </div>
        </div>

        {/* Charts Section */}
        <div className="card">
          <h3 className="text-xl font-bold text-gray-900 mb-6">Incident Response Overview</h3>
          <p className="text-sm text-gray-600 mb-6">
            Visual representation of trends and response time
          </p>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Bar Chart - Real Emergencies vs Prank Calls */}
            <div>
              <h4 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-orange-500" />
                Real Emergencies vs Prank Calls
              </h4>
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={emergencyData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis dataKey="month" tick={{ fill: '#6b7280', fontSize: 12 }} />
                  <YAxis tick={{ fill: '#6b7280', fontSize: 12 }} />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: '#fff', 
                      border: '1px solid #e5e7eb',
                      borderRadius: '8px'
                    }} 
                  />
                  <Bar dataKey="emergencies" fill="#6b7280" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="pranks" fill="#9ca3af" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Area Chart - Response Time Improvement */}
            <div>
              <h4 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-green-500" />
                Response Time Improvement
              </h4>
              <ResponsiveContainer width="100%" height={250}>
                <AreaChart data={responseData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis dataKey="month" tick={{ fill: '#6b7280', fontSize: 12 }} />
                  <YAxis tick={{ fill: '#6b7280', fontSize: 12 }} />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: '#fff', 
                      border: '1px solid #e5e7eb',
                      borderRadius: '8px'
                    }} 
                  />
                  <Area 
                    type="monotone" 
                    dataKey="time" 
                    stroke="#d1d5db" 
                    fill="#e5e7eb"
                    strokeWidth={2}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* Recent Calls Section */}
        <div className="card">
          <h3 className="text-xl font-bold text-gray-900 mb-2">Recent Calls</h3>
          <p className="text-sm text-gray-600 mb-6">
            Overview of the latest recent calls handled
          </p>

          <div className="space-y-3">
            {recentCalls.map((call, index) => (
              <div
                key={index}
                className="flex items-center gap-4 p-4 bg-gray-50 rounded-lg border border-gray-200"
              >
                <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${
                  call.color === 'red' ? 'bg-red-100' :
                  call.color === 'yellow' ? 'bg-yellow-100' : 'bg-blue-100'
                }`}>
                  {call.color === 'red' && <AlertTriangle className="w-6 h-6 text-red-600" />}
                  {call.color === 'yellow' && <Clock className="w-6 h-6 text-yellow-600" />}
                  {call.color === 'blue' && <CheckCircle className="w-6 h-6 text-blue-600" />}
                </div>
                <div className="flex-1">
                  <p className="font-semibold text-gray-900">{call.date}</p>
                  <p className="text-sm text-gray-600">{call.time}</p>
                </div>
                <div className="text-right">
                  <p className={`font-semibold ${
                    call.color === 'red' ? 'text-red-600' :
                    call.color === 'yellow' ? 'text-yellow-600' : 'text-blue-600'
                  }`}>
                    Urgency Level: {call.level}
                  </p>
                  <p className="text-sm text-gray-600">{call.status}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div className="text-center text-sm text-gray-500 py-4">
          <p>This document and its information are confidential and for authorized viewing only.</p>
          <div className="flex items-center justify-center gap-4 mt-2">
            <span>© 2025 Rescue AI</span>
            <span>•</span>
            <a href="#" className="hover:text-gray-700">Privacy Policy</a>
            <span>•</span>
            <a href="#" className="hover:text-gray-700">Terms of Service</a>
          </div>
        </div>
      </div>
    </Layout>
  )
}
