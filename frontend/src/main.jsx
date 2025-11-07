import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'
import { SENTRY_DSN } from './env'

// Initialize client-side Sentry only when a DSN is provided.
let Sentry = null
try {
  if (SENTRY_DSN) {
    // Dynamic import so that Sentry packages are only required when the DSN is set.
    // This keeps the dev/build lightweight when Sentry is not used.
    // Note: @sentry/react and @sentry/tracing must be present in package.json for this to work.
    Sentry = await import('@sentry/react')
    const Tracing = await import('@sentry/tracing')
    Sentry.init({
      dsn: SENTRY_DSN,
      integrations: [new Tracing.BrowserTracing()],
      tracesSampleRate: parseFloat(import.meta.env.VITE_SENTRY_TRACES_SAMPLE_RATE || '0.0'),
      environment: import.meta.env.MODE || 'production',
    })
    console.info('Sentry initialized (frontend)')
  }
} catch (err) {
  // If Sentry packages are not installed or initialization fails, don't block the app.
  console.warn('Failed to initialize client-side Sentry:', err)
  Sentry = null
}

const root = ReactDOM.createRoot(document.getElementById('root'))
root.render(
  <React.StrictMode>
    {Sentry ? <Sentry.ErrorBoundary fallback={<div>Something went wrong</div>}><App /></Sentry.ErrorBoundary> : <App />}
  </React.StrictMode>,
)

