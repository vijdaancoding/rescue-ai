import { useState } from 'react'
import Layout from '../components/Layout'
import { Phone, PhoneOff, Clock, Calendar, Filter, Download, Search } from 'lucide-react'

export default function CallHistory() {
  const [searchTerm, setSearchTerm] = useState('')
  const [filterType, setFilterType] = useState('all')

  const callHistoryData = [
    {
      id: 1,
      date: '2025-02-06',
      time: '14:32',
      duration: '5:43',
      type: 'emergency',
      operatorId: 'OP-1122',
      status: 'Dispatched',
      priority: 'High',
      location: 'Downtown Lahore'
    },
    {
      id: 2,
      date: '2025-02-06',
      time: '13:45',
      duration: '2:15',
      type: 'prank',
      operatorId: 'OP-1123',
      status: 'Blocked',
      priority: 'Low',
      location: 'Unknown'
    },
    {
      id: 3,
      date: '2025-02-06',
      time: '12:18',
      duration: '8:20',
      type: 'emergency',
      operatorId: 'OP-1124',
      status: 'Completed',
      priority: 'Medium',
      location: 'Model Town'
    },
    {
      id: 4,
      date: '2025-02-05',
      time: '18:55',
      duration: '3:30',
      type: 'emergency',
      operatorId: 'OP-1122',
      status: 'Dispatched',
      priority: 'High',
      location: 'Johar Town'
    },
    {
      id: 5,
      date: '2025-02-05',
      time: '16:22',
      duration: '1:05',
      type: 'prank',
      operatorId: 'OP-1125',
      status: 'Blocked',
      priority: 'Low',
      location: 'Unknown'
    },
  ]

  const filteredCalls = callHistoryData.filter(call => {
    const matchesSearch = call.location.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         call.operatorId.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesFilter = filterType === 'all' || call.type === filterType
    return matchesSearch && matchesFilter
  })

  return (
    <Layout title="Call History">
      <div className="space-y-6">
        {/* Header with Actions */}
        <div className="card">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <h2 className="text-2xl font-bold text-gray-900 mb-2">Call History Log</h2>
              <p className="text-gray-600">Complete record of all emergency calls received</p>
            </div>
            <button className="btn btn-primary flex items-center gap-2">
              <Download className="w-4 h-4" />
              Export Report
            </button>
          </div>
        </div>

        {/* Filters and Search */}
        <div className="card">
          <div className="flex flex-col md:flex-row gap-4">
            {/* Search */}
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search by location or operator ID..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-900"
              />
            </div>

            {/* Filter */}
            <div className="flex items-center gap-2">
              <Filter className="w-4 h-4 text-gray-600" />
              <select
                value={filterType}
                onChange={(e) => setFilterType(e.target.value)}
                className="px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-900"
              >
                <option value="all">All Calls</option>
                <option value="emergency">Emergencies Only</option>
                <option value="prank">Prank Calls Only</option>
              </select>
            </div>
          </div>
        </div>

        {/* Call History Table */}
        <div className="card overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-left py-3 px-4 font-semibold text-gray-700">Date & Time</th>
                <th className="text-left py-3 px-4 font-semibold text-gray-700">Duration</th>
                <th className="text-left py-3 px-4 font-semibold text-gray-700">Type</th>
                <th className="text-left py-3 px-4 font-semibold text-gray-700">Operator</th>
                <th className="text-left py-3 px-4 font-semibold text-gray-700">Priority</th>
                <th className="text-left py-3 px-4 font-semibold text-gray-700">Location</th>
                <th className="text-left py-3 px-4 font-semibold text-gray-700">Status</th>
              </tr>
            </thead>
            <tbody>
              {filteredCalls.map((call) => (
                <tr key={call.id} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="py-4 px-4">
                    <div className="flex items-center gap-2">
                      <Calendar className="w-4 h-4 text-gray-400" />
                      <div>
                        <p className="font-medium text-gray-900">{call.date}</p>
                        <p className="text-sm text-gray-500">{call.time}</p>
                      </div>
                    </div>
                  </td>
                  <td className="py-4 px-4">
                    <div className="flex items-center gap-2">
                      <Clock className="w-4 h-4 text-gray-400" />
                      <span className="text-gray-700">{call.duration}</span>
                    </div>
                  </td>
                  <td className="py-4 px-4">
                    <div className="flex items-center gap-2">
                      {call.type === 'emergency' ? (
                        <>
                          <Phone className="w-4 h-4 text-green-600" />
                          <span className="text-green-600 font-medium">Emergency</span>
                        </>
                      ) : (
                        <>
                          <PhoneOff className="w-4 h-4 text-red-600" />
                          <span className="text-red-600 font-medium">Prank</span>
                        </>
                      )}
                    </div>
                  </td>
                  <td className="py-4 px-4">
                    <span className="text-gray-700 font-mono text-sm">{call.operatorId}</span>
                  </td>
                  <td className="py-4 px-4">
                    <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                      call.priority === 'High' ? 'bg-red-100 text-red-700' :
                      call.priority === 'Medium' ? 'bg-yellow-100 text-yellow-700' :
                      'bg-gray-100 text-gray-700'
                    }`}>
                      {call.priority}
                    </span>
                  </td>
                  <td className="py-4 px-4">
                    <span className="text-gray-700">{call.location}</span>
                  </td>
                  <td className="py-4 px-4">
                    <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                      call.status === 'Dispatched' ? 'bg-blue-100 text-blue-700' :
                      call.status === 'Completed' ? 'bg-green-100 text-green-700' :
                      'bg-gray-100 text-gray-700'
                    }`}>
                      {call.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {filteredCalls.length === 0 && (
            <div className="text-center py-12">
              <Phone className="w-12 h-12 text-gray-400 mx-auto mb-3" />
              <p className="text-gray-600">No calls found matching your criteria</p>
            </div>
          )}
        </div>

        {/* Statistics */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="card text-center">
            <p className="text-3xl font-bold text-gray-900 mb-2">
              {callHistoryData.length}
            </p>
            <p className="text-sm text-gray-600">Total Calls</p>
          </div>
          <div className="card text-center">
            <p className="text-3xl font-bold text-green-600 mb-2">
              {callHistoryData.filter(c => c.type === 'emergency').length}
            </p>
            <p className="text-sm text-gray-600">Emergencies</p>
          </div>
          <div className="card text-center">
            <p className="text-3xl font-bold text-red-600 mb-2">
              {callHistoryData.filter(c => c.type === 'prank').length}
            </p>
            <p className="text-sm text-gray-600">Prank Calls</p>
          </div>
          <div className="card text-center">
            <p className="text-3xl font-bold text-blue-600 mb-2">
              {callHistoryData.filter(c => c.status === 'Dispatched').length}
            </p>
            <p className="text-sm text-gray-600">Dispatched</p>
          </div>
        </div>
      </div>
    </Layout>
  )
}
