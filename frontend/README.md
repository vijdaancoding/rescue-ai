# 🚨 Rescue AI - Emergency Dispatcher Dashboard

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![React](https://img.shields.io/badge/React-18.2.0-blue.svg)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.2.2-blue.svg)](https://www.typescriptlang.org/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind-3.4.1-38B2AC.svg)](https://tailwindcss.com/)

A modern, professional emergency dispatcher dashboard system built with React, TypeScript, and Tailwind CSS. This application provides real-time call management, Urdu transcription, AI-powered analytics, and comprehensive emergency response coordination for Rescue 1122 and emergency services.

## 🚀 Features

### 🔐 Authentication
- Secure operator login system
- Operator ID and password authentication
- Session management

### 📊 Dashboard
- **Live View**: Real-time monitoring of waiting calls
- **System Health**: Active units, latency monitoring, and status indicators
- **Interactive Map**: Visual representation of ambulance positions
- **Incoming Call Alerts**: Click-to-answer functionality with animated indicators

### 📞 Live Call Management
- **Urdu Transcription**: Real-time speech-to-text in Urdu language
- **Sound Wave Visualizer**: Live audio waveform display
- **Situation Overview**: AI-powered threat probability analysis (34% critical detection)
- **Quick Actions**: Dispatch unit or mark as false alarm

### 📈 Analytics
- **Incident Analytics**: Comprehensive data visualization
- **Real Emergencies vs Prank Calls**: Bar chart comparison
- **Response Time Trends**: Area chart showing improvement over time
- **Recent Calls Log**: Detailed call history with urgency levels

### 📋 Call History
- Complete call log with filtering and search
- Export functionality for reports
- Detailed information: date, time, duration, operator, priority, location, status
- Real-time statistics dashboard

### ⚙️ Settings
- **Profile Management**: Update operator information
- **Notifications**: Configure sound alerts, email notifications, emergency alerts
- **Display**: Dark mode toggle, language selection (English, Urdu, Punjabi)
- **Audio**: Volume control, microphone permissions
- **Security**: Two-factor authentication, session timeout configuration

## 🛠️ Tech Stack

- **Frontend Framework**: React 18.2.0
- **Language**: TypeScript
- **Routing**: React Router DOM 6.22.0
- **Styling**: Tailwind CSS 3.4.1
- **Charts**: Recharts 2.12.0
- **Icons**: Lucide React 0.344.0
- **Build Tool**: Vite 5.1.4

## 📦 Installation

### Prerequisites
- Node.js (v18 or higher)
- npm or yarn package manager

### Setup Instructions

1. **Install Dependencies**
   ```bash
   npm install
   ```

2. **Start Development Server**
   ```bash
   npm run dev
   ```
   The application will open automatically at `http://localhost:3000`

3. **Build for Production**
   ```bash
   npm run build
   ```

4. **Preview Production Build**
   ```bash
   npm run preview
   ```

## 🗂️ Project Structure

```
rescue-ai-dispatcher/
├── src/
│   ├── components/
│   │   └── Layout.tsx          # Reusable layout with sidebar
│   ├── pages/
│   │   ├── SignIn.tsx          # Login page
│   │   ├── Dashboard.tsx       # Main dashboard/live view
│   │   ├── Analytics.tsx       # Analytics and reports
│   │   ├── LiveCall.tsx        # Active call handling
│   │   ├── CallHistory.tsx     # Call history log
│   │   └── Settings.tsx        # Settings and preferences
│   ├── App.tsx                 # Main app with routing
│   ├── main.tsx                # Application entry point
│   └── index.css               # Global styles and Tailwind
├── index.html
├── package.json
├── tsconfig.json
├── tailwind.config.js
├── vite.config.ts
└── README.md
```

## 🎯 Usage

### Login
1. Navigate to the application
2. Enter Operator ID and Password
3. Click "Enter Command Center"
4. You'll be redirected to the Dashboard

### Handling Calls
1. From the Dashboard, incoming calls appear with a pulsing red indicator
2. Click on an incoming call to view details
3. Navigate to the Live Call page to see transcription and take action
4. Choose to "Dispatch Unit" or mark as "False Alarm"

### Viewing Analytics
1. Navigate to Analytics from the sidebar
2. View charts for emergency trends and response times
3. Export reports using the "Export Report" button

### Managing Call History
1. Navigate to Call History
2. Use search to filter by location or operator ID
3. Filter by call type (All, Emergencies, Prank Calls)
4. Export detailed reports

### Configuring Settings
1. Navigate to Settings
2. Update profile information
3. Configure notifications, display, audio, and security preferences
4. Click "Save All Settings" to apply changes

## 🎨 Design Features

- **Modern UI**: Clean, professional interface with smooth animations
- **Responsive Design**: Works seamlessly on desktop, tablet, and mobile
- **Accessibility**: High contrast, clear typography, keyboard navigation
- **Real-time Updates**: Live data visualization and call monitoring
- **Intuitive Navigation**: Clear sidebar navigation with active state indicators

## 🔒 Security Features

- Operator authentication system
- Session timeout configuration
- Two-factor authentication option
- Authorized personnel access control
- Secure data handling

## 📱 Responsive Design

The application is fully responsive and optimized for:
- Desktop (1920px and above)
- Laptop (1024px - 1919px)
- Tablet (768px - 1023px)
- Mobile (320px - 767px)

## 🌐 Supported Languages

- English (Default)
- اردو (Urdu)
- ਪੰਜਾਬੀ (Punjabi)

## 🚦 Routes

- `/` - Redirects to sign-in
- `/signin` - Login page
- `/dashboard` - Main dashboard (Live View)
- `/analytics` - Analytics and reports
- `/live` - Active call handling
- `/call-history` - Call history log
- `/settings` - Settings and preferences

## 🎓 FYP Project Notes

This is a Final Year Project (FYP) showcasing:
- Full-stack frontend development skills
- Modern React architecture with TypeScript
- Responsive design principles
- Data visualization
- Real-time system monitoring
- Emergency response system design

## 📝 Future Enhancements

- Backend API integration
- Real-time WebSocket connections
- Advanced AI transcription
- Multi-language support expansion
- Mobile app version
- Advanced analytics with ML predictions
- Integration with emergency services databases

## 👨‍💻 Development

### Code Quality
- TypeScript for type safety
- ESLint for code linting
- Consistent code formatting
- Component-based architecture
- Reusable components

### Performance
- Vite for fast development and building
- Code splitting with React Router
- Optimized bundle size
- Lazy loading for routes

## 📄 License

This is a university FYP project. All rights reserved.

## 🙏 Acknowledgments

- Rescue 1122 for inspiration
- Emergency services personnel
- University supervisors and mentors

---

**Built with ❤️ for Emergency Response Services**
