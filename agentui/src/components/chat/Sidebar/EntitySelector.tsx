'use client'

import * as React from 'react'
import {
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem
} from '@/components/ui/select'
import { useStore } from '@/store'
import { useQueryState } from 'nuqs'
import Icon from '@/components/ui/icon'
import { useEffect } from 'react'
import useChatActions from '@/hooks/useChatActions'

export function EntitySelector() {
  const { agents, setMessages, setSelectedModel } = useStore()

  const { focusChatInput } = useChatActions()
  const [agentId, setAgentId] = useQueryState('agent', {
    parse: (value) => value || undefined,
    history: 'push'
  })
  const [, setSessionId] = useQueryState('session')

  useEffect(() => {
    if (agents.length > 0) {
      if (!agentId) {
        const defaultEntity = agents[0]
        setAgentId(defaultEntity.id)
      } else {
        const entity = agents.find((item) => item.id === agentId)
        if (entity) {
          setSelectedModel(entity.model?.model || '')
          if (entity.model?.model) {
            focusChatInput()
          }
        }
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [agentId, agents, setSelectedModel])

  const handleOnValueChange = (value: string) => {
    const newValue = value === agentId ? null : value
    const selectedEntity = agents.find((item) => item.id === newValue)

    setSelectedModel(selectedEntity?.model?.provider || '')
    setAgentId(newValue)

    setMessages([])
    setSessionId(null)

    if (selectedEntity?.model?.provider) {
      focusChatInput()
    }
  }

  if (agents.length === 0) {
    return (
      <Select disabled>
        <SelectTrigger className="h-9 w-full rounded-md border border-hairline bg-surface-card text-ink text-xs font-medium uppercase opacity-50">
          <SelectValue placeholder="No Agents Available" />
        </SelectTrigger>
      </Select>
    )
  }

  return (
    <Select
      value={agentId || ''}
      onValueChange={(value) => handleOnValueChange(value)}
    >
      <SelectTrigger className="h-9 w-full rounded-md border border-hairline bg-surface-card text-ink text-xs font-medium uppercase">
        <SelectValue placeholder="Select Agent" />
      </SelectTrigger>
      <SelectContent className="border border-hairline bg-canvas text-ink shadow-none rounded-md">
        {agents.map((entity, index) => (
          <SelectItem
            className="cursor-pointer"
            key={`${entity.id}-${index}`}
            value={entity.id}
          >
            <div className="flex items-center gap-3 text-xs font-medium uppercase">
              <Icon type={'user'} size="xs" />
              {entity.name || entity.id}
            </div>
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )
}
