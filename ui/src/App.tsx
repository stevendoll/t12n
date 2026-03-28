import { useState, useEffect } from 'react'
import Cursor from './components/Cursor'
import Home from './pages/Home'
import HistoryPage from './pages/HistoryPage'
import AdminPage from './pages/AdminPage'

function useHashRoute() {
  const [hash, setHash] = useState(window.location.hash)
  useEffect(() => {
    const handler = () => setHash(window.location.hash)
    window.addEventListener('hashchange', handler)
    return () => window.removeEventListener('hashchange', handler)
  }, [])
  return hash
}

export default function App() {
  const hash = useHashRoute()
  const page = hash === '#/history' ? 'history'
             : hash === '#/admin'   ? 'admin'
             : 'home'

  return (
    <>
      <Cursor />
      <div className="fixed inset-0 pointer-events-none z-0 bg-[image:linear-gradient(var(--border)_1px,transparent_1px),linear-gradient(90deg,var(--border)_1px,transparent_1px)] bg-[size:80px_80px] [mask-image:radial-gradient(ellipse_at_center,transparent_30%,black_100%)]" />
      {page === 'history' ? <HistoryPage />
     : page === 'admin'   ? <AdminPage />
     : <Home />}
    </>
  )
}
