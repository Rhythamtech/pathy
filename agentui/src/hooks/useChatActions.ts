import { useCallback } from 'react'
import { toast } from 'sonner'

import { useStore } from '../store'

import { type AgentDetails, type ChatMessage } from '@/types/os'
import { getAgentsAPI, getStatusAPI } from '@/api/os'
import { useQueryState } from 'nuqs'

const useChatActions = () => {
  const { chatInputRef } = useStore()
  const selectedEndpoint = useStore((state) => state.selectedEndpoint)
  const authToken = useStore((state) => state.authToken)
  const [, setSessionId] = useQueryState('session')
  const setMessages = useStore((state) => state.setMessages)
  const setIsEndpointActive = useStore((state) => state.setIsEndpointActive)
  const setIsEndpointLoading = useStore((state) => state.setIsEndpointLoading)
  const setAgents = useStore((state) => state.setAgents)
  const setSelectedModel = useStore((state) => state.setSelectedModel)
  const [agentId, setAgentId] = useQueryState('agent')
  const [, setDbId] = useQueryState('db_id')

  const getStatus = useCallback(async () => {
    try {
      const status = await getStatusAPI(selectedEndpoint, authToken)
      return status
    } catch {
      return 503
    }
  }, [selectedEndpoint, authToken])

  const getAgents = useCallback(async () => {
    try {
      const agents = await getAgentsAPI(selectedEndpoint, authToken)
      return agents
    } catch {
      toast.error('Error fetching agents')
      return []
    }
  }, [selectedEndpoint, authToken])

  const clearChat = useCallback(() => {
    setMessages([])
    setSessionId(null)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const focusChatInput = useCallback(() => {
    setTimeout(() => {
      requestAnimationFrame(() => chatInputRef?.current?.focus())
    }, 0)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const addMessage = useCallback(
    (message: ChatMessage) => {
      setMessages((prevMessages) => [...prevMessages, message])
    },
    [setMessages]
  )

  const initialize = useCallback(async () => {
    setIsEndpointLoading(true)
    try {
      const status = await getStatus()
      let agents: AgentDetails[] = []
      if (status === 200) {
        setIsEndpointActive(true)
        agents = await getAgents()

        if (!agentId && agents.length > 0) {
          const firstAgent = agents[0]
          setAgentId(firstAgent.id)
          setSelectedModel(firstAgent.model?.model || '')
          setDbId(firstAgent.db_id || '')
          setAgents(agents)
        } else {
          setAgents(agents)
          if (agentId) {
            const agent = agents.find((a) => a.id === agentId)
            if (agent) {
              setSelectedModel(agent.model?.model || '')
              setDbId(agent.db_id || '')
            } else if (agents.length > 0) {
              const firstAgent = agents[0]
              setAgentId(firstAgent.id)
              setSelectedModel(firstAgent.model?.model || '')
              setDbId(firstAgent.db_id || '')
            }
          }
        }
      } else {
        setIsEndpointActive(false)
        setSelectedModel('')
        setAgentId(null)
      }
      return { agents }
    } catch (error) {
      console.error('Error initializing :', error)
      setIsEndpointActive(false)
      setSelectedModel('')
      setAgentId(null)
      setAgents([])
    } finally {
      setIsEndpointLoading(false)
    }
  }, [
    getStatus,
    getAgents,
    setIsEndpointActive,
    setIsEndpointLoading,
    setAgents,
    setAgentId,
    setSelectedModel,
    setDbId,
    agentId
  ])

  return {
    clearChat,
    addMessage,
    getAgents,
    focusChatInput,
    initialize
  }
}

export default useChatActions
