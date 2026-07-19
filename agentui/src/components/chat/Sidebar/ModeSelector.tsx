'use client'

import { useStore } from '@/store'

export function ModeSelector() {
  const mode = useStore((state) => state.mode)

  return (
    <div className="flex h-9 w-full items-center rounded-md border border-hairline bg-surface-card px-3 text-xs font-medium uppercase text-ink">
      {mode}
    </div>
  )
}
