import { useEffect, useState } from "react"
import { motion } from "framer-motion"
import { GraduationCap, FlaskConical } from "lucide-react"

const STUDENTS = 6
const LABS = 4

// A fixed, hand-picked matching so the animation always resolves cleanly.
const MATCHES: [number, number][] = [
  [0, 0], [1, 0], [2, 1], [3, 2], [4, 2], [5, 3],
]

export function HeroGraphAnimation() {
  const [activeStep, setActiveStep] = useState(0)

  useEffect(() => {
    const id = setInterval(() => {
      setActiveStep((s) => (s + 1) % (MATCHES.length + 2))
    }, 850)
    return () => clearInterval(id)
  }, [])

  const width = 480
  const height = 360
  const studentX = 60
  const labX = width - 60
  const studentGap = height / (STUDENTS + 1)
  const labGap = height / (LABS + 1)

  return (
    <div className="relative mx-auto w-full max-w-[480px]">
      <svg viewBox={`0 0 ${width} ${height}`} className="w-full">
        {MATCHES.map(([s, l], idx) => {
          const revealed = idx < activeStep
          const y1 = studentGap * (s + 1)
          const y2 = labGap * (l + 1)
          return (
            <motion.line
              key={idx}
              x1={studentX}
              y1={y1}
              x2={labX}
              y2={y2}
              stroke={revealed ? "#3987e5" : "#2c2c2a"}
              strokeWidth={revealed ? 2 : 1}
              strokeDasharray={revealed ? "0" : "4 4"}
              initial={{ pathLength: 0, opacity: 0 }}
              animate={{ pathLength: revealed ? 1 : 0.3, opacity: revealed ? 0.9 : 0.25 }}
              transition={{ duration: 0.6 }}
            />
          )
        })}

        {Array.from({ length: STUDENTS }).map((_, i) => (
          <motion.circle
            key={`s${i}`}
            cx={studentX}
            cy={studentGap * (i + 1)}
            r={14}
            fill="#12121a"
            stroke="#6366f1"
            strokeWidth={1.5}
            animate={{ scale: [1, 1.08, 1] }}
            transition={{ duration: 2.4, repeat: Infinity, delay: i * 0.15 }}
          />
        ))}
        {Array.from({ length: LABS }).map((_, i) => (
          <motion.circle
            key={`l${i}`}
            cx={labX}
            cy={labGap * (i + 1)}
            r={16}
            fill="#12121a"
            stroke="#9085e9"
            strokeWidth={1.5}
            animate={{ scale: [1, 1.1, 1] }}
            transition={{ duration: 2.8, repeat: Infinity, delay: i * 0.2 }}
          />
        ))}
      </svg>

      {Array.from({ length: STUDENTS }).map((_, i) => (
        <div
          key={`si${i}`}
          className="absolute flex h-7 w-7 -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full text-brand-400"
          style={{ left: `${(studentX / width) * 100}%`, top: `${(studentGap * (i + 1) / height) * 100}%` }}
        >
          <GraduationCap className="h-3.5 w-3.5" />
        </div>
      ))}
      {Array.from({ length: LABS }).map((_, i) => (
        <div
          key={`li${i}`}
          className="absolute flex h-8 w-8 -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full text-violet-400"
          style={{ left: `${(labX / width) * 100}%`, top: `${(labGap * (i + 1) / height) * 100}%` }}
        >
          <FlaskConical className="h-4 w-4" />
        </div>
      ))}
    </div>
  )
}
