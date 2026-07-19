import Icon from '@/components/ui/icon'
import MarkdownRenderer from '@/components/ui/typography/MarkdownRenderer'
import { useStore } from '@/store'
import type { ChatMessage } from '@/types/os'
import Videos from './Multimedia/Videos'
import Images from './Multimedia/Images'
import Audios from './Multimedia/Audios'
import { memo, useState, useRef, useEffect } from 'react'
import AgentThinkingLoader from './AgentThinkingLoader'
import { toast } from 'sonner'
import { stripMarkdown } from '@/lib/utils'


interface MessageProps {
  message: ChatMessage
}

const CopyButton = ({ text }: { text: string }) => {
  const [isOpen, setIsOpen] = useState(false)
  const [copiedType, setCopiedType] = useState<'markdown' | 'text' | null>(null)
  const menuRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }
    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside)
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [isOpen])

  const handleCopy = async (type: 'markdown' | 'text') => {
    try {
      const contentToCopy = type === 'markdown' ? text : stripMarkdown(text)
      await navigator.clipboard.writeText(contentToCopy)
      setCopiedType(type)
      toast.success(
        type === 'markdown'
          ? 'Copied response as Markdown!'
          : 'Copied response as Plain Text!'
      )
      setIsOpen(false)
      setTimeout(() => setCopiedType(null), 2000)
    } catch {
      toast.error('Failed to copy response.')
    }
  }

  return (
    <div className="relative inline-block text-left" ref={menuRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex size-7 items-center justify-center rounded-md border border-hairline bg-surface-card hover:bg-surface-soft text-mute hover:text-ink transition-colors focus:outline-none"
        title="Copy response"
        aria-label="Copy response"
      >
        {copiedType ? (
          <Icon type="check" size="xxs" className="text-accent" />
        ) : (
          <Icon type="copy" size="xxs" />
        )}
      </button>

      {isOpen && (
        <div className="absolute left-0 mt-1 z-50 w-44 rounded-lg border border-hairline bg-canvas p-1 shadow-lg ring-1 ring-black/5 focus:outline-none animate-in fade-in slide-in-from-top-1 duration-150">
          <button
            onClick={() => handleCopy('markdown')}
            className="flex w-full items-center gap-2 rounded-md px-3 py-1.5 text-xs text-ink hover:bg-surface-soft text-left transition-colors font-sans"
          >
            <Icon type="copy" size="xxs" className="text-mute" />
            <span>Copy as Markdown</span>
          </button>
          <button
            onClick={() => handleCopy('text')}
            className="flex w-full items-center gap-2 rounded-md px-3 py-1.5 text-xs text-ink hover:bg-surface-soft text-left transition-colors font-sans"
          >
            <Icon type="file-text" size="xxs" className="text-mute" />
            <span>Copy as Plain Text</span>
          </button>
        </div>
      )}
    </div>
  )
}

const AgentMessage = ({ message }: MessageProps) => {
  const { streamingErrorMessage } = useStore()
  let messageContent
  if (message.streamingError) {
    messageContent = (
      <p className="text-danger text-sm">
        Something went wrong while streaming.{' '}
        {streamingErrorMessage ? (
          <>{streamingErrorMessage}</>
        ) : (
          'Please try refreshing the page or try again later.'
        )}
      </p>
    )
  } else if (message.content) {
    messageContent = (
      <div className="flex w-full flex-col gap-4">
        <MarkdownRenderer>{message.content}</MarkdownRenderer>
        {message.videos && message.videos.length > 0 && (
          <Videos videos={message.videos} />
        )}
        {message.images && message.images.length > 0 && (
          <Images images={message.images} />
        )}
        {message.audio && message.audio.length > 0 && (
          <Audios audio={message.audio} />
        )}
      </div>
    )
  } else if (message.response_audio) {
    if (!message.response_audio.transcript) {
      messageContent = (
        <div className="mt-2 flex items-start">
          <AgentThinkingLoader />
        </div>
      )
    } else {
      messageContent = (
        <div className="flex w-full flex-col gap-4">
          <MarkdownRenderer>
            {message.response_audio.transcript}
          </MarkdownRenderer>
          {message.response_audio.content && message.response_audio && (
            <Audios audio={[message.response_audio]} />
          )}
        </div>
      )
    }
  } else {
    messageContent = (
      <div className="mt-2">
        <AgentThinkingLoader />
      </div>
    )
  }

  const rawTextContent = message.content || message.response_audio?.transcript || ''
  const hasCopyableContent = !!rawTextContent && !message.streamingError

  return (
    <div className="flex flex-row items-start gap-4 font-sans w-full group relative">
      <div className="flex-shrink-0 mt-1">
        <div className="flex size-8 items-center justify-center rounded-lg bg-accent/10 text-accent">
          <Icon type="agent" size="xs" />
        </div>
      </div>
      <div className="flex flex-col gap-2 w-full min-w-0">
        {messageContent}
        {hasCopyableContent && (
          <div className="flex items-center gap-2 mt-1">
            <CopyButton text={rawTextContent} />
          </div>
        )}
      </div>
    </div>
  )
}

const UserMessage = memo(({ message }: MessageProps) => {
  return (
    <div className="flex items-start gap-4 pt-4 text-start max-md:break-words">
      <div className="flex-shrink-0 mt-1">
        <div className="flex size-8 items-center justify-center rounded-lg bg-surface-card border border-hairline text-ink">
          <Icon type="user" size="xs" />
        </div>
      </div>
      <div className="text-md rounded-md font-sans text-body leading-relaxed">
        {message.content}
      </div>
    </div>
  )
})

AgentMessage.displayName = 'AgentMessage'
UserMessage.displayName = 'UserMessage'
export { AgentMessage, UserMessage }
