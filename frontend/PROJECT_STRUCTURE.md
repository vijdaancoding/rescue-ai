# 📁 Project Structure

```
rescue-ai/
├── 📂 public/                    # Static assets served at root
│   └── favicon.svg              # Custom app icon
│
├── 📂 src/
│   ├── 📂 assets/               # Application assets
│   │   ├── images/              # Image files
│   │   └── icons/               # Icon files
│   │
│   ├── 📂 components/           # Reusable UI components
│   │   ├── Layout.tsx           # Main layout wrapper
│   │   ├── ProtectedRoute.tsx   # Route protection
│   │   └── Toast.tsx            # Toast notification
│   │
│   ├── 📂 context/              # React Context providers
│   │   └── AuthContext.tsx      # Authentication state
│   │
│   ├── 📂 pages/                # Page components (routes)
│   │   ├── SignIn.tsx           # Login page
│   │   ├── Dashboard.tsx        # Main dashboard
│   │   ├── LiveCall.tsx         # Active call handler
│   │   ├── Analytics.tsx        # Analytics & reports
│   │   ├── CallHistory.tsx      # Call logs
│   │   └── Settings.tsx         # User settings
│   │
│   ├── 📂 hooks/                # Custom React hooks
│   │   └── useToast.ts          # Toast notifications hook
│   │
│   ├── 📂 lib/                  # Utility functions
│   │   └── utils.ts             # Helper functions
│   │
│   ├── 📂 types/                # TypeScript definitions
│   │   └── index.ts             # Type definitions
│   │
│   ├── 📂 constants/            # Application constants
│   │   └── index.ts             # Constants & config
│   │
│   ├── App.tsx                  # Main app component
│   ├── main.tsx                 # Entry point
│   └── index.css                # Global styles
│
├── 📂 .vscode/                  # VSCode configuration
│   ├── settings.json            # Editor settings
│   └── extensions.json          # Recommended extensions
│
├── 📄 index.html                # HTML template
├── 📄 package.json              # Dependencies
├── 📄 tsconfig.json             # TypeScript config
├── 📄 tailwind.config.js        # Tailwind config
├── 📄 vite.config.ts            # Vite config
├── 📄 vercel.json               # Vercel deployment
│
├── 📄 README.md                 # Main documentation
├── 📄 CONTRIBUTING.md           # Contribution guide
├── 📄 LICENSE                   # MIT License
├── 📄 .gitignore                # Git ignore rules
├── 📄 .gitattributes            # Git attributes
└── 📄 .env.example              # Environment template
```

## 🎯 Key Improvements

### ✅ Professional Organization
- **Separated concerns** with dedicated folders
- **Clear naming conventions** for easy navigation
- **Scalable structure** ready for team collaboration

### ✅ Development Tools
- **VSCode settings** for consistent formatting
- **TypeScript types** for better code quality
- **Custom hooks** for reusable logic
- **Utility functions** in dedicated lib folder

### ✅ Documentation
- **README** with badges and clear instructions
- **CONTRIBUTING** guide for collaborators
- **LICENSE** for open source clarity
- **PROJECT_STRUCTURE** for easy onboarding

### ✅ Configuration
- **Environment template** for easy setup
- **Vercel config** for deployment
- **Git attributes** for cross-platform compatibility
- **Professional .gitignore** with comprehensive rules

## 🚀 Benefits

1. **Easy to Navigate** - Clear folder structure
2. **Scalable** - Ready for growth and new features
3. **Professional** - Industry-standard organization
4. **Well-Documented** - Clear guides for all aspects
5. **Type-Safe** - TypeScript throughout
6. **Maintainable** - Clean code organization
