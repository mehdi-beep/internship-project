import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import dayjs from 'dayjs'
import isoWeek from 'dayjs/plugin/isoWeek'
import './index.css'
import App from './App.tsx'

// ISO/Monday-start weeks — matches the backend's date.weekday()-based week
// boundary (Monday=0), so frontend week selection and backend week
// aggregation agree on the same 7-day windows.
dayjs.extend(isoWeek)

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
