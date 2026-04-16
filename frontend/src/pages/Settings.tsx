import { useState } from 'react'
import Layout from '../components/Layout'
import { User, Bell, Shield, Globe, Moon, Volume2, Save } from 'lucide-react'

export default function Settings() {
  const [settings, setSettings] = useState({
    // Profile
    operatorName: 'Operator 1122',
    operatorId: 'OP-1122',
    email: 'operator1122@rescue.ai',
    
    // Notifications
    soundAlerts: true,
    emailNotifications: true,
    emergencyAlerts: true,
    
    // Display
    darkMode: false,
    language: 'english',
    
    // Audio
    volume: 75,
    microphone: true,
    
    // Security
    twoFactorAuth: true,
    sessionTimeout: 30,
  })

  const handleSave = () => {
    // Save settings logic here
    alert('Settings saved successfully!')
  }

  return (
    <Layout title="Settings">
      <div className="space-y-6">
        {/* Header */}
        <div className="card">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Settings & Preferences</h2>
          <p className="text-gray-600">Customize your Rescue AI experience</p>
        </div>

        {/* Profile Settings */}
        <div className="card">
          <div className="flex items-center gap-3 mb-6">
            <User className="w-6 h-6 text-gray-700" />
            <h3 className="text-xl font-bold text-gray-900">Profile Information</h3>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Operator Name
              </label>
              <input
                type="text"
                value={settings.operatorName}
                onChange={(e) => setSettings({ ...settings, operatorName: e.target.value })}
                className="input-field"
              />
            </div>
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Operator ID
              </label>
              <input
                type="text"
                value={settings.operatorId}
                disabled
                className="input-field bg-gray-100 cursor-not-allowed"
              />
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Email Address
              </label>
              <input
                type="email"
                value={settings.email}
                onChange={(e) => setSettings({ ...settings, email: e.target.value })}
                className="input-field"
              />
            </div>
          </div>
        </div>

        {/* Notification Settings */}
        <div className="card">
          <div className="flex items-center gap-3 mb-6">
            <Bell className="w-6 h-6 text-gray-700" />
            <h3 className="text-xl font-bold text-gray-900">Notifications</h3>
          </div>

          <div className="space-y-4">
            <div className="flex items-center justify-between py-3 border-b border-gray-200">
              <div>
                <p className="font-medium text-gray-900">Sound Alerts</p>
                <p className="text-sm text-gray-600">Play sound for incoming calls</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={settings.soundAlerts}
                  onChange={(e) => setSettings({ ...settings, soundAlerts: e.target.checked })}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-gray-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-black"></div>
              </label>
            </div>

            <div className="flex items-center justify-between py-3 border-b border-gray-200">
              <div>
                <p className="font-medium text-gray-900">Email Notifications</p>
                <p className="text-sm text-gray-600">Receive updates via email</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={settings.emailNotifications}
                  onChange={(e) => setSettings({ ...settings, emailNotifications: e.target.checked })}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-gray-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-black"></div>
              </label>
            </div>

            <div className="flex items-center justify-between py-3">
              <div>
                <p className="font-medium text-gray-900">Emergency Alerts</p>
                <p className="text-sm text-gray-600">High priority emergency notifications</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={settings.emergencyAlerts}
                  onChange={(e) => setSettings({ ...settings, emergencyAlerts: e.target.checked })}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-gray-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-black"></div>
              </label>
            </div>
          </div>
        </div>

        {/* Display Settings */}
        <div className="card">
          <div className="flex items-center gap-3 mb-6">
            <Moon className="w-6 h-6 text-gray-700" />
            <h3 className="text-xl font-bold text-gray-900">Display & Language</h3>
          </div>

          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-gray-900">Dark Mode</p>
                <p className="text-sm text-gray-600">Switch to dark theme</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={settings.darkMode}
                  onChange={(e) => setSettings({ ...settings, darkMode: e.target.checked })}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-gray-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-black"></div>
              </label>
            </div>

            <div className="flex items-center gap-3">
              <Globe className="w-5 h-5 text-gray-600" />
              <div className="flex-1">
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Interface Language
                </label>
                <select
                  value={settings.language}
                  onChange={(e) => setSettings({ ...settings, language: e.target.value })}
                  className="input-field"
                >
                  <option value="english">English</option>
                  <option value="urdu">اردو (Urdu)</option>
                  <option value="punjabi">ਪੰਜਾਬੀ (Punjabi)</option>
                </select>
              </div>
            </div>
          </div>
        </div>

        {/* Audio Settings */}
        <div className="card">
          <div className="flex items-center gap-3 mb-6">
            <Volume2 className="w-6 h-6 text-gray-700" />
            <h3 className="text-xl font-bold text-gray-900">Audio Settings</h3>
          </div>

          <div className="space-y-6">
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-3">
                System Volume: {settings.volume}%
              </label>
              <input
                type="range"
                min="0"
                max="100"
                value={settings.volume}
                onChange={(e) => setSettings({ ...settings, volume: parseInt(e.target.value) })}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-black"
              />
            </div>

            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-gray-900">Microphone Access</p>
                <p className="text-sm text-gray-600">Allow microphone for voice commands</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={settings.microphone}
                  onChange={(e) => setSettings({ ...settings, microphone: e.target.checked })}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-gray-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-black"></div>
              </label>
            </div>
          </div>
        </div>

        {/* Security Settings */}
        <div className="card">
          <div className="flex items-center gap-3 mb-6">
            <Shield className="w-6 h-6 text-gray-700" />
            <h3 className="text-xl font-bold text-gray-900">Security</h3>
          </div>

          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-gray-900">Two-Factor Authentication</p>
                <p className="text-sm text-gray-600">Add an extra layer of security</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={settings.twoFactorAuth}
                  onChange={(e) => setSettings({ ...settings, twoFactorAuth: e.target.checked })}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-gray-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-black"></div>
              </label>
            </div>

            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Session Timeout (minutes)
              </label>
              <input
                type="number"
                value={settings.sessionTimeout}
                onChange={(e) => setSettings({ ...settings, sessionTimeout: parseInt(e.target.value) })}
                className="input-field"
                min="5"
                max="120"
              />
            </div>
          </div>
        </div>

        {/* Save Button */}
        <div className="card">
          <button
            onClick={handleSave}
            className="btn btn-primary w-full md:w-auto flex items-center justify-center gap-2"
          >
            <Save className="w-4 h-4" />
            Save All Settings
          </button>
        </div>
      </div>
    </Layout>
  )
}
