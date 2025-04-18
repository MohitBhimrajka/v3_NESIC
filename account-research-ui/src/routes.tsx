import { createBrowserRouter } from 'react-router-dom'
import { AppShell } from './layouts/AppShell'
import { Outlet } from 'react-router-dom'
import { lazy } from 'react'

// Lazy load pages
const LandingPage = lazy(() => import('./pages/LandingPage'))
const WizardLayout = lazy(() => import('./pages/WizardLayout'))
const ProgressPage = lazy(() => import('./pages/ProgressPage'))
const ResultPage = lazy(() => import('./pages/ResultPage'))
const HistoryPage = lazy(() => import('./pages/HistoryPage'))

const Shell = () => (
  <AppShell>
    <Outlet />
  </AppShell>
)

export const router = createBrowserRouter([
  {
    path: '/',
    element: <Shell />,
    children: [
      {
        index: true,
        element: <LandingPage />,
      },
      {
        path: 'generate/*',
        element: <WizardLayout />,
      },
      {
        path: 'task/:id',
        element: <ProgressPage />,
      },
      {
        path: 'task/:id/result',
        element: <ResultPage />,
      },
      {
        path: 'history',
        element: <HistoryPage />,
      },
    ],
  },
]) 