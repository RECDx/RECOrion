import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import './theme/palette.generated.css'
import './theme/theme.css'
import './ui/ui.css'
import './ui/responsive.css'
import App from './App.jsx'
import FeedbackHost from './ui/FeedbackHost.jsx'
import { initTheme } from './theme/theme.js'

initTheme()

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
    <FeedbackHost />
  </StrictMode>,
)
