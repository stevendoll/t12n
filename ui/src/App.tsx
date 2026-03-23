import Cursor from './components/Cursor'
import Home from './pages/Home'

export default function App() {
  return (
    <>
      <Cursor />
      <div className="fixed inset-0 pointer-events-none z-0 bg-[image:linear-gradient(var(--border)_1px,transparent_1px),linear-gradient(90deg,var(--border)_1px,transparent_1px)] bg-[size:80px_80px] [mask-image:radial-gradient(ellipse_at_center,transparent_30%,black_100%)]" />
      <Home />
    </>
  )
}
