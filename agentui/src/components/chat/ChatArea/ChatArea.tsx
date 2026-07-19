'use client'

import ChatInput from './ChatInput'
import MessageArea from './MessageArea'
import { useStore } from '@/store'
import Icon from '@/components/ui/icon'
import { Button } from '@/components/ui/button'

const ChatArea = () => {
  const setIsSidebarOpen = useStore((state) => state.setIsSidebarOpen)

  return (
    <main className="relative flex flex-grow flex-col bg-canvas min-w-0">
      {/* Mobile Header */}
      <div className="md:hidden flex items-center justify-between px-4 py-3 border-b border-hairline bg-surface-card">
        <div className="flex items-center gap-1.5">
          <img src="/logo.svg" className="size-6 object-contain invert dark:invert-0" alt="Pathy Logo" />
          <span className="text-sm font-bold uppercase tracking-wider text-ink">Pathy</span>
          <span className="text-sm font-medium uppercase tracking-wider text-charcoal">Roadmap</span>
        </div>
        <Button 
          variant="ghost" 
          size="icon" 
          onClick={() => setIsSidebarOpen(true)}
          className="h-8 w-8 text-ink"
        >
          <Icon type="menu" size="sm" />
        </Button>
      </div>
      
      <MessageArea />
      <div className="sticky bottom-0 px-2 md:px-4 pb-2">
        <ChatInput />
      </div>
    </main>
  )
}

export default ChatArea
