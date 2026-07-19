'use client'

import { motion } from 'framer-motion'
import React from 'react'

const ChatBlankState = () => {
  return (
    <section
      className="flex flex-col items-center justify-center text-center font-sans h-full max-w-2xl mx-auto py-12 px-4"
      aria-label="Welcome message"
    >
      <div className="flex flex-col gap-y-6">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5 }}
          className="mx-auto flex h-16 w-16 items-center justify-center"
        >
          <img src="/logo.svg" className="size-16 object-contain invert dark:invert-0" alt="Pathy Logo" />
        </motion.div>

        <motion.h1
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className="text-4xl font-bold tracking-tight text-ink"
        >
          Pathy RoadMap AI
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.3 }}
          className="text-base text-body max-w-md mx-auto leading-relaxed"
        >
          Welcome! I am Pathy, your learning assistant. Let me help you build a personalized, week-by-week learning roadmap for any topic you want to master.
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.4 }}
          className="mt-4 flex flex-col items-start gap-4 p-8 rounded-lg bg-surface-card border border-hairline text-left text-sm text-body max-w-xl mx-auto"
        >
          <div className="font-bold uppercase text-accent tracking-wider">How to get started</div>
          <ul className="space-y-3 text-body leading-normal list-none pl-0">
            <li className="flex items-start gap-2">
              <span className="text-accent text-base leading-none select-none font-bold">+</span>
              <span>
                Type what you want to learn (e.g. <code className="bg-surface-soft px-1.5 py-0.5 rounded font-mono text-ink text-xs">FastAPI</code> or <code className="bg-surface-soft px-1.5 py-0.5 rounded font-mono text-ink text-xs">Machine Learning</code>).
              </span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-accent text-base leading-none select-none font-bold">+</span>
              <span>Specify your skill level, target outcomes, and preferred language.</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-accent text-base leading-none select-none font-bold">+</span>
              <span>Wait as I find top YouTube creators, courses, Reddit reviews, rank them, and structure a custom week-by-week curriculum!</span>
            </li>
          </ul>
        </motion.div>
      </div>
    </section>
  )
}

export default ChatBlankState
