import type { CSSProperties } from 'react'

interface LogoProps {
  className?: string
  style?: CSSProperties
}

/**
 * AegisSOC AI Geometric Shield + Stylized "A" Mark
 * Scalable vector mark designed for cybersecurity enterprise aesthetics.
 */
export function AegisMark({ className, style }: LogoProps) {
  return (
    <svg
      className={className}
      style={style}
      viewBox="0 0 100 100"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      <defs>
        <linearGradient id="aegis-shield-grad" x1="10%" y1="0%" x2="90%" y2="100%">
          <stop offset="0%" stopColor="#00F0FF" />
          <stop offset="50%" stopColor="#00A2FF" />
          <stop offset="100%" stopColor="#0051FF" />
        </linearGradient>
        <linearGradient id="aegis-inner-grad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#00F5FF" />
          <stop offset="100%" stopColor="#0088FF" />
        </linearGradient>
        <linearGradient id="aegis-glow" x1="50%" y1="0%" x2="50%" y2="100%">
          <stop offset="0%" stopColor="#00F0FF" stopOpacity="0.25" />
          <stop offset="100%" stopColor="#0051FF" stopOpacity="0" />
        </linearGradient>
      </defs>

      {/* Outer Shield Outline */}
      <path
        d="M50 4L88 19V54C88 75.5 50 96 50 96C50 96 12 75.5 12 54V19L50 4Z"
        stroke="url(#aegis-shield-grad)"
        strokeWidth="5"
        strokeLinejoin="round"
        fill="url(#aegis-glow)"
      />

      {/* Corner Tech Facets / Circuit Notches */}
      <path d="M22 24L50 13L78 24" stroke="url(#aegis-inner-grad)" strokeWidth="2.5" strokeLinecap="round" opacity="0.8" />
      <path d="M18 52C18 69 44 86 50 89C56 86 82 69 82 52" stroke="url(#aegis-inner-grad)" strokeWidth="2" strokeLinecap="round" opacity="0.6" />

      {/* Stylized Cyber "A" Core */}
      <path
        d="M50 22L72 68H60L50 46L40 68H28L50 22Z"
        fill="url(#aegis-inner-grad)"
      />
      {/* A Crossbar Tech Element */}
      <path
        d="M37 57H63L65 62H35L37 57Z"
        fill="#00F0FF"
      />
      {/* Glowing Central Diamond Node */}
      <polygon
        points="50,38 55,45 50,52 45,45"
        fill="#FFFFFF"
      />
    </svg>
  )
}

/**
 * AegisSOC AI Full Logo (Mark + Typography Wordmark)
 */
export function AegisLogo({ className, style }: LogoProps) {
  return (
    <svg
      className={className}
      style={style}
      viewBox="0 0 350 80"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      role="img"
      aria-label="AegisSOC AI"
    >
      <defs>
        <linearGradient id="aegis-full-grad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#00F0FF" />
          <stop offset="50%" stopColor="#00A2FF" />
          <stop offset="100%" stopColor="#0051FF" />
        </linearGradient>
        <linearGradient id="aegis-ai-badge" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stopColor="#00F0FF" />
          <stop offset="100%" stopColor="#0088FF" />
        </linearGradient>
      </defs>

      {/* Embedded Mark */}
      <g transform="translate(4, 5) scale(0.7)">
        <path
          d="M50 4L88 19V54C88 75.5 50 96 50 96C50 96 12 75.5 12 54V19L50 4Z"
          stroke="url(#aegis-full-grad)"
          strokeWidth="5"
          strokeLinejoin="round"
          fill="rgba(0, 240, 255, 0.12)"
        />
        <path d="M22 24L50 13L78 24" stroke="url(#aegis-full-grad)" strokeWidth="2.5" strokeLinecap="round" opacity="0.8" />
        <path
          d="M50 22L72 68H60L50 46L40 68H28L50 22Z"
          fill="url(#aegis-full-grad)"
        />
        <path
          d="M37 57H63L65 62H35L37 57Z"
          fill="#00F0FF"
        />
        <polygon
          points="50,38 55,45 50,52 45,45"
          fill="#FFFFFF"
        />
      </g>

      {/* Typography: "Aegis" */}
      <text
        x="84"
        y="50"
        fill="currentColor"
        fontFamily="Inter, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
        fontSize="34"
        fontWeight="800"
        letterSpacing="-0.03em"
      >
        Aegis
      </text>

      {/* Typography: "SOC" */}
      <text
        x="172"
        y="50"
        fill="url(#aegis-full-grad)"
        fontFamily="Inter, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
        fontSize="34"
        fontWeight="800"
        letterSpacing="0.02em"
      >
        SOC
      </text>

      {/* Badge: "AI" */}
      <g transform="translate(254, 25)">
        <rect
          x="0"
          y="0"
          width="44"
          height="27"
          rx="6"
          fill="url(#aegis-ai-badge)"
        />
        <text
          x="22"
          y="18.5"
          fill="#0B0F19"
          fontFamily="Inter, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
          fontSize="15"
          fontWeight="900"
          letterSpacing="0.05em"
          textAnchor="middle"
        >
          AI
        </text>
      </g>
    </svg>
  )
}

// Aliases for seamless drop-in backwards compatibility with existing codebase imports
export const AegisSOCMark = AegisMark
export const AegisSOCLogo = AegisLogo
