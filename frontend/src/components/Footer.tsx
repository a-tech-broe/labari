export default function Footer() {
  return (
    <footer className="border-t border-dim mt-20">
      <div className="max-w-4xl mx-auto px-4 py-6 text-center text-sm text-muted">
        &copy; {new Date().getFullYear()} Labari &mdash; Built on AWS
      </div>
    </footer>
  )
}
