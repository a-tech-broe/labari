import Link from 'next/link'

export default function Header() {
  return (
    <header className="sticky top-0 z-50 border-b border-dim bg-[#0a0a0a]/80 backdrop-blur-sm">
      <div className="max-w-4xl mx-auto px-4 h-14 flex items-center justify-between">
        <Link href="/" className="text-xl font-bold tracking-tight hover:text-accent transition-colors">
          Labari
          <span className="text-accent">.</span>
        </Link>
        <nav className="flex items-center gap-6 text-sm text-muted">
          <Link href="/" className="hover:text-[var(--text)] transition-colors">Home</Link>
          <Link href="/admin/" className="hover:text-[var(--text)] transition-colors">Admin</Link>
        </nav>
      </div>
    </header>
  )
}
