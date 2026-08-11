import { Link } from '../catalyst-ui-kit/typescript/link'
import { Text } from '../catalyst-ui-kit/typescript/text'

export default function Footer() {
  return (
    <footer className="mt-auto bg-cyber-surface border-t border-cyber-border py-8">
      <div className="max-w-6xl mx-auto px-6 flex flex-col sm:flex-row items-center justify-between gap-4">
        <Text className="text-sm">
          &copy; {new Date().getFullYear()} Joseph Prince. All rights reserved.
        </Text>
        <div className="flex gap-6">
          <Link
            href="/resume"
            className="text-text-muted hover:text-neon-cyan transition-colors text-sm"
          >
            R&eacute;sum&eacute;
          </Link>
          <Link
            href="https://linkedin.com/in/thejprince"
            target="_blank"
            rel="noopener noreferrer"
            className="text-text-muted hover:text-neon-cyan transition-colors text-sm"
          >
            LinkedIn
          </Link>
          <Link
            href="https://github.com/dedrozs"
            target="_blank"
            rel="noopener noreferrer"
            className="text-text-muted hover:text-neon-cyan transition-colors text-sm"
          >
            GitHub
          </Link>
        </div>
      </div>
    </footer>
  )
}
