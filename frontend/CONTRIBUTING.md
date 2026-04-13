# Contributing to Rescue AI

Thank you for your interest in contributing to the Rescue AI Emergency Dispatcher Dashboard!

## Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/behram7cr/rescue-ai.git
   cd rescue-ai
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Start development server**
   ```bash
   npm run dev
   ```

## Project Structure

```
rescue-ai/
├── public/              # Static assets
├── src/
│   ├── assets/         # Images, icons, fonts
│   ├── components/     # Reusable UI components
│   ├── context/        # React context providers
│   ├── constants/      # Application constants
│   ├── hooks/          # Custom React hooks
│   ├── lib/            # Utility functions
│   ├── pages/          # Page components
│   ├── types/          # TypeScript type definitions
│   ├── App.tsx         # Main app component
│   ├── main.tsx        # Application entry point
│   └── index.css       # Global styles
├── package.json        # Dependencies and scripts
├── tsconfig.json       # TypeScript configuration
├── tailwind.config.js  # Tailwind CSS configuration
└── vite.config.ts      # Vite configuration
```

## Code Standards

- **TypeScript**: Use TypeScript for all new files
- **Components**: Use functional components with hooks
- **Styling**: Use Tailwind CSS utility classes
- **Naming**: Use PascalCase for components, camelCase for functions
- **Formatting**: Follow the existing code style

## Making Changes

1. Create a new branch for your feature
2. Make your changes
3. Test thoroughly
4. Commit with clear messages
5. Push and create a pull request

## Questions?

Feel free to open an issue for any questions or concerns.
