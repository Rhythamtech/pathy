'use client'
import { Button } from '@/components/ui/button'
import { useTheme } from 'next-themes'
import { ModeSelector } from '@/components/chat/Sidebar/ModeSelector'
import { EntitySelector } from '@/components/chat/Sidebar/EntitySelector'
import useChatActions from '@/hooks/useChatActions'
import { useStore } from '@/store'
import { motion, AnimatePresence } from 'framer-motion'
import { useState, useEffect } from 'react'
import Icon from '@/components/ui/icon'
import { getProviderIcon } from '@/lib/modelProvider'
import Sessions from './Sessions'
import AuthToken from './AuthToken'
import { cn, isValidUrl, truncateText } from '@/lib/utils'
import { toast } from 'sonner'
import { useQueryState } from 'nuqs'
import { Skeleton } from '@/components/ui/skeleton'

const ENDPOINT_PLACEHOLDER = 'NO ENDPOINT ADDED'
const SidebarHeader = () => (
  <div className="flex items-center gap-1.5">
    <img src="/logo.svg" className="size-7 object-contain invert dark:invert-0" alt="Pathy Logo" />
    <span className="text-sm font-bold uppercase tracking-wider text-ink">Pathy</span>
    <span className="text-sm font-medium uppercase tracking-wider text-charcoal">Roadmap</span>
  </div>
)

const NewChatButton = ({
  disabled,
  onClick
}: {
  disabled: boolean
  onClick: () => void
}) => (
  <Button
    onClick={onClick}
    disabled={disabled}
    className="w-full h-9 rounded-md bg-accent px-[20px] text-sm font-medium text-white hover:brightness-110 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
  >
    <span className="mr-2 text-lg leading-none">+</span>
    <span className="tracking-wide">New Chat</span>
  </Button>
)

const ModelDisplay = ({ model }: { model: string }) => (
  <div className="flex h-9 w-full items-center gap-3 rounded-md border border-hairline bg-surface-card p-3 text-xs font-medium uppercase text-ink">
    {(() => {
      const icon = getProviderIcon(model)
      return icon ? <Icon type={icon} className="shrink-0" size="xs" /> : null
    })()}
    {model}
  </div>
)

const Endpoint = () => {
  const {
    selectedEndpoint,
    isEndpointActive,
    setSelectedEndpoint,
    setAgents,
    setSessionsData,
    setMessages
  } = useStore()
  const { initialize } = useChatActions()
  const [isEditing, setIsEditing] = useState(false)
  const [endpointValue, setEndpointValue] = useState('')
  const [isMounted, setIsMounted] = useState(false)
  const [isHovering, setIsHovering] = useState(false)
  const [isRotating, setIsRotating] = useState(false)
  const [, setAgentId] = useQueryState('agent')
  const [, setSessionId] = useQueryState('session')

  useEffect(() => {
    setEndpointValue(selectedEndpoint)
    setIsMounted(true)
  }, [selectedEndpoint])

  const getStatusColor = (isActive: boolean) =>
    isActive ? 'bg-positive' : 'bg-destructive'

  const handleSave = async () => {
    if (!isValidUrl(endpointValue)) {
      toast.error('Please enter a valid URL')
      return
    }
    const cleanEndpoint = endpointValue.replace(/\/$/, '').trim()
    setSelectedEndpoint(cleanEndpoint)
    setAgentId(null)
    setSessionId(null)
    setIsEditing(false)
    setIsHovering(false)
    setAgents([])
    setSessionsData([])
    setMessages([])
  }

  const handleCancel = () => {
    setEndpointValue(selectedEndpoint)
    setIsEditing(false)
    setIsHovering(false)
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      handleSave()
    } else if (e.key === 'Escape') {
      handleCancel()
    }
  }

  const handleRefresh = async () => {
    setIsRotating(true)
    await initialize()
    setTimeout(() => setIsRotating(false), 500)
  }

  return (
    <div className="flex flex-col items-start gap-2">
      <div className="text-xs font-medium uppercase text-accent">Pathy OS</div>
      {isEditing ? (
        <div className="flex w-full items-center gap-1">
          <input
            type="text"
            value={endpointValue}
            onChange={(e) => setEndpointValue(e.target.value)}
            onKeyDown={handleKeyDown}
            className="flex h-9 w-full items-center text-ellipsis rounded-md border border-accent/20 bg-surface-card p-3 text-xs font-medium text-muted"
            autoFocus
          />
          <Button
            variant="ghost"
            size="icon"
            onClick={handleSave}
            className="hover:cursor-pointer hover:bg-surface-soft"
          >
            <Icon type="save" size="xs" />
          </Button>
        </div>
      ) : (
        <div className="flex w-full items-center gap-1">
          <motion.div
            className="relative flex h-9 w-full cursor-pointer items-center justify-between rounded-md border border-hairline bg-surface-card p-3 uppercase"
            onMouseEnter={() => setIsHovering(true)}
            onMouseLeave={() => setIsHovering(false)}
            onClick={() => setIsEditing(true)}
            transition={{ type: 'spring', stiffness: 400, damping: 10 }}
          >
            <AnimatePresence mode="wait">
              {isHovering ? (
                <motion.div
                  key="endpoint-display-hover"
                  className="absolute inset-0 flex items-center justify-center"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 0.2 }}
                >
                  <p className="flex items-center gap-2 whitespace-nowrap text-xs font-medium text-accent">
                    <Icon type="edit" size="xxs" /> EDIT PATHY OS
                  </p>
                </motion.div>
              ) : (
                <motion.div
                  key="endpoint-display"
                  className="absolute inset-0 flex items-center justify-between px-3"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 0.2 }}
                >
                  <p className="text-xs font-medium text-body">
                    {isMounted
                      ? truncateText(selectedEndpoint, 21) ||
                        ENDPOINT_PLACEHOLDER
                      : 'http://localhost:7777'}
                  </p>
                  <div
                    className={`size-2 shrink-0 rounded-full ${getStatusColor(isEndpointActive)}`}
                  />
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
          <Button
            variant="ghost"
            size="icon"
            onClick={handleRefresh}
            className="hover:cursor-pointer hover:bg-surface-soft"
          >
            <motion.div
              key={isRotating ? 'rotating' : 'idle'}
              animate={{ rotate: isRotating ? 360 : 0 }}
              transition={{ duration: 0.5, ease: 'easeInOut' }}
            >
              <Icon type="refresh" size="xs" />
            </motion.div>
          </Button>
        </div>
      )}
    </div>
  )
}

const ThemeToggle = () => {
  const { theme, setTheme } = useTheme()
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  if (!mounted) return null

  return (
    <Button
      variant="ghost"
      onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
      className="flex w-full items-center justify-between rounded-md border border-hairline bg-surface-card p-2.5 text-xs text-ink hover:bg-surface-soft hover:text-ink"
    >
      <span className="uppercase font-medium">Theme</span>
      <div className="flex items-center gap-1.5 font-medium uppercase">
        {theme === 'dark' ? (
          <>
            <Icon type="moon" size="xs" />
            <span>Dark</span>
          </>
        ) : (
          <>
            <Icon type="sun" size="xs" />
            <span>Light</span>
          </>
        )}
      </div>
    </Button>
  )
}

import ApiConfigModal from './ApiConfigModal'
import { Settings } from 'lucide-react'

const Sidebar = ({
  hasEnvToken,
  envToken
}: {
  hasEnvToken?: boolean
  envToken?: string
}) => {
  const [isCollapsed, setIsCollapsed] = useState(false)
  const [isConfigModalOpen, setIsConfigModalOpen] = useState(false)
  const { clearChat, focusChatInput, initialize } = useChatActions()
  const {
    messages,
    selectedEndpoint,
    isEndpointActive,
    selectedModel,
    hydrated,
    isEndpointLoading,
    isSidebarOpen,
    setIsSidebarOpen
  } = useStore()
  const [isMounted, setIsMounted] = useState(false)
  const [agentId] = useQueryState('agent')

  useEffect(() => {
    setIsMounted(true)

    if (hydrated) initialize()
  }, [selectedEndpoint, initialize, hydrated])

  const handleNewChat = () => {
    clearChat()
    focusChatInput()
  }

  return (
    <>
      {/* Mobile Backdrop */}
      {isSidebarOpen && (
        <div 
          className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm md:hidden transition-opacity"
          onClick={() => setIsSidebarOpen(false)}
        />
      )}
      
      <motion.aside
        className={cn(
          'absolute md:relative z-50 flex h-[100dvh] max-h-[100dvh] shrink-0 grow-0 flex-col overflow-hidden px-3 py-3 bg-canvas md:bg-transparent border-r border-hairline md:border-none shadow-2xl md:shadow-none transition-transform duration-300 md:translate-x-0',
          isSidebarOpen ? 'translate-x-0' : '-translate-x-full'
        )}
        initial={{ width: '16rem' }}
        animate={{ width: isCollapsed ? '2.5rem' : '16rem' }}
        transition={{ type: 'spring', stiffness: 300, damping: 30 }}
      >
      <motion.button
        onClick={() => setIsCollapsed(!isCollapsed)}
        className="hidden md:block absolute right-2 top-2 z-10 p-1 text-mute hover:text-ink"
        aria-label={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        type="button"
        whileTap={{ scale: 0.95 }}
      >
        <Icon
          type="sheet"
          size="xs"
          className={`transform ${isCollapsed ? 'rotate-180' : 'rotate-0'}`}
        />
      </motion.button>
      <motion.div
        className="flex flex-col h-full w-60 justify-between"
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: isCollapsed ? 0 : 1, x: isCollapsed ? -20 : 0 }}
        transition={{ duration: 0.3, ease: 'easeInOut' }}
        style={{
          pointerEvents: isCollapsed ? 'none' : 'auto'
        }}
      >
        <div className="flex flex-col flex-1 overflow-y-auto space-y-5 pr-1 py-2">
          <SidebarHeader />
          <NewChatButton
            disabled={messages.length === 0}
            onClick={handleNewChat}
          />
          {isMounted && (
            <>

              {isEndpointActive && (
                <>
                  <motion.div
                    className="flex w-full flex-col items-start gap-2"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ duration: 0.5, ease: 'easeInOut' }}
                  >
                    <div className="text-xs font-medium uppercase text-accent mb-1">
                      Mode
                    </div>
                    {isEndpointLoading ? (
                      <div className="flex w-full flex-col gap-2">
                        {Array.from({ length: 3 }).map((_, index) => (
                          <Skeleton
                            key={index}
                            className="h-9 w-full rounded-md"
                          />
                        ))}
                      </div>
                    ) : (
                      <>
                        <ModeSelector />
                        <EntitySelector />
                        {selectedModel && agentId && (
                          <ModelDisplay model={selectedModel} />
                        )}
                      </>
                    )}
                  </motion.div>
                  <Sessions />
                </>
              )}
            </>
          )}
        </div>
        <div className="pt-4 border-t border-hairline space-y-2">
          <Button
            variant="ghost"
            onClick={() => setIsConfigModalOpen(true)}
            className="flex w-full items-center justify-between rounded-md border border-hairline bg-surface-card p-2.5 text-xs text-ink hover:bg-surface-soft hover:text-ink"
          >
            <span className="uppercase font-medium">AI Endpoint</span>
            <div className="flex items-center gap-1.5 font-medium uppercase text-accent">
              <Settings className="size-3.5 text-accent animate-spin-hover" />
              <span>Configure</span>
            </div>
          </Button>
          <ThemeToggle />
          <ApiConfigModal isOpen={isConfigModalOpen} onOpenChange={setIsConfigModalOpen} />
        </div>
      </motion.div>
    </motion.aside>
    </>
  )
}

export default Sidebar
