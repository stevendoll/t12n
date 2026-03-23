export default function Nav() {
  return (
    <nav className="fixed top-0 left-0 right-0 z-50 flex justify-between items-center px-12 py-7 border-b border-[var(--border)] backdrop-blur-md bg-[rgba(5,79,89,0.7)]">
      <a href="#" className="flex items-center no-underline">
        <img src="/assets/t12n-ai-name.png" alt="t12n.ai" className="h-[19px] w-auto" />
      </a>
      <ul className="list-none flex gap-10">
        <li><a href="#about" className="text-[rgba(245,240,232,0.5)] no-underline text-[0.72rem] tracking-[0.12em] uppercase transition-colors hover:text-[var(--accent)]">About</a></li>
        <li><a href="#services" className="text-[rgba(245,240,232,0.5)] no-underline text-[0.72rem] tracking-[0.12em] uppercase transition-colors hover:text-[var(--accent)]">Services</a></li>
        <li><a href="mailto:hello@t12n.ai" className="text-[rgba(245,240,232,0.5)] no-underline text-[0.72rem] tracking-[0.12em] uppercase transition-colors hover:text-[var(--accent)]">Contact</a></li>
      </ul>
    </nav>
  )
}
