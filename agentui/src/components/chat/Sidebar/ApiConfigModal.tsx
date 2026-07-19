'use client'

import React, { useState, useEffect, useCallback } from 'react'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { APIRoutes } from '@/api/routes'
import { useStore } from '@/store'
import { toast } from 'sonner'
import { Loader2, Settings, ShieldAlert, Key, Globe, Cpu } from 'lucide-react'
import useChatActions from '@/hooks/useChatActions'

// Simple custom Input wrapper in case Input is not available
const CustomInput = React.forwardRef<HTMLInputElement, React.InputHTMLAttributes<HTMLInputElement>>(
  ({ type, ...props }, ref) => {
    return (
      <input
        type={type}
        className="flex h-9 w-full rounded-md border border-hairline bg-surface-soft px-3 py-1 text-sm shadow-sm transition-colors placeholder:text-muted focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent disabled:cursor-not-allowed disabled:opacity-50 text-ink"
        ref={ref}
        {...props}
      />
    )
  }
)
CustomInput.displayName = 'CustomInput'

interface ApiConfigModalProps {
  isOpen: boolean
  onOpenChange: (open: boolean) => void
}

export default function ApiConfigModal({ isOpen, onOpenChange }: ApiConfigModalProps) {
  const { selectedEndpoint, authToken } = useStore()
  const { initialize } = useChatActions()
  
  const [apiKey, setApiKey] = useState('')
  const [baseUrl, setBaseUrl] = useState('')
  const [modelName, setModelName] = useState('')
  
  const [isLoading, setIsLoading] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [validationError, setValidationError] = useState<string | null>(null)
  
  const [status, setStatus] = useState<{
    is_configured: boolean
    model_name: string | null
    base_url: string | null
    api_key_preview: string | null
    source: 'env' | 'user' | 'none'
  } | null>(null)

  // Fetch current config status from backend
  const fetchConfigStatus = useCallback(async () => {
    setIsLoading(true)
    setValidationError(null)
    try {
      const res = await fetch(APIRoutes.ConfigGet(selectedEndpoint), {
        headers: {
          'Content-Type': 'application/json',
          ...(authToken ? { Authorization: `Bearer ${authToken}` } : {})
        }
      })
      if (res.ok) {
        const data = await res.json()
        setStatus(data)
        setBaseUrl(data.base_url || '')
        setModelName(data.model_name || '')
        setApiKey(data.api_key_preview ? '••••••••••••••••' : '')
      }
    } catch (err) {
      console.error('Failed to fetch config status', err)
    } finally {
      setIsLoading(false)
    }
  }, [selectedEndpoint, authToken])

  useEffect(() => {
    if (isOpen) {
      fetchConfigStatus()
    }
  }, [isOpen, fetchConfigStatus])

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault()
    setValidationError(null)
    setIsSaving(true)

    // Basic client-side checks
    if (!baseUrl.trim()) {
      setValidationError('Base URL is required.')
      setIsSaving(false)
      return
    }
    if (!apiKey.trim()) {
      setValidationError('API Key is required.')
      setIsSaving(false)
      return
    }
    if (!modelName.trim()) {
      setValidationError('Model Name is required.')
      setIsSaving(false)
      return
    }

    try {
      const res = await fetch(APIRoutes.ConfigSet(selectedEndpoint), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(authToken ? { Authorization: `Bearer ${authToken}` } : {})
        },
        body: JSON.stringify({
          api_key: apiKey === '••••••••••••••••' ? '' : apiKey, // keep old if unchanged, or send new
          base_url: baseUrl,
          model_name: modelName
        })
      })

      const data = await res.json()
      if (res.ok) {
        toast.success('API credentials validated & saved successfully!')
        initialize() // refresh endpoints and model display
        onOpenChange(false)
      } else {
        setValidationError(data.detail || 'Validation failed.')
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err)
      setValidationError(msg || 'An error occurred while connecting to the server.')
    } finally {
      setIsSaving(false)
    }
  }

  const handleClear = async () => {
    setValidationError(null)
    setIsSaving(true)
    try {
      const res = await fetch(APIRoutes.ConfigClear(selectedEndpoint), {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
          ...(authToken ? { Authorization: `Bearer ${authToken}` } : {})
        }
      })
      if (res.ok) {
        toast.success('Cleared overrides, reverted to environment configuration.')
        initialize() // refresh endpoints and model display
        fetchConfigStatus()
      } else {
        const data = await res.json()
        setValidationError(data.detail || 'Failed to clear config.')
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err)
      setValidationError(msg || 'An error occurred.')
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <Dialog open={isOpen} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-[480px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-xl text-ink">
            <Settings className="size-5 text-accent animate-pulse" />
            AI Endpoint Configuration
          </DialogTitle>
          <DialogDescription className="text-charcoal text-xs mt-1">
            Provide credentials for any OpenAI-compatible API (e.g. OpenRouter, DeepSeek, Local LLM, or custom gateways). Overrides will be verified and held securely in-memory on the backend.
          </DialogDescription>
        </DialogHeader>

        {isLoading ? (
          <div className="flex h-48 items-center justify-center">
            <Loader2 className="size-8 animate-spin text-accent" />
          </div>
        ) : (
          <form onSubmit={handleSave} className="space-y-4">
            {/* Status Display */}
            {status && (
              <div className="rounded-lg bg-surface-soft p-3 border border-hairline flex items-center justify-between text-xs">
                <div className="flex items-center gap-2">
                  <div className={`size-2 rounded-full ${status.is_configured ? 'bg-positive' : 'bg-destructive animate-ping'}`} />
                  <span className="font-semibold uppercase tracking-wider text-charcoal">
                    {status.is_configured ? 'Configured' : 'Not Configured'}
                  </span>
                </div>
                {status.source !== 'none' && (
                  <span className="rounded bg-accent/15 px-2 py-0.5 text-[10px] font-bold uppercase text-accent">
                    Source: {status.source}
                  </span>
                )}
              </div>
            )}

            {/* Error Message Box */}
            {validationError && (
              <div className="rounded-lg bg-destructive/10 border border-destructive/20 p-3 flex gap-2.5 text-xs text-destructive">
                <ShieldAlert className="size-4 shrink-0 mt-0.5" />
                <div className="flex-1 font-medium">{validationError}</div>
              </div>
            )}

            {/* Form Fields */}
            <div className="space-y-3.5">
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-charcoal flex items-center gap-1.5 uppercase tracking-wider">
                  <Globe className="size-3.5 text-accent" />
                  Base URL
                </label>
                <CustomInput
                  value={baseUrl}
                  onChange={(e) => setBaseUrl(e.target.value)}
                  placeholder="https://api.openai.com/v1"
                  disabled={isSaving}
                  required
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-charcoal flex items-center gap-1.5 uppercase tracking-wider">
                  <Key className="size-3.5 text-accent" />
                  API Key
                </label>
                <CustomInput
                  type="password"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  placeholder="sk-..."
                  disabled={isSaving}
                  required
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-charcoal flex items-center gap-1.5 uppercase tracking-wider">
                  <Cpu className="size-3.5 text-accent" />
                  Model Name
                </label>
                <CustomInput
                  value={modelName}
                  onChange={(e) => setModelName(e.target.value)}
                  placeholder="gpt-4o"
                  disabled={isSaving}
                  required
                />
              </div>
            </div>

            <DialogFooter className="pt-4 border-t border-hairline mt-5 flex flex-row items-center justify-end gap-2 sm:space-x-0">
              {status?.source === 'user' && (
                <Button
                  type="button"
                  variant="outline"
                  onClick={handleClear}
                  disabled={isSaving}
                  className="mr-auto text-xs h-9"
                >
                  Clear Overrides
                </Button>
              )}
              <Button
                type="button"
                variant="ghost"
                onClick={() => onOpenChange(false)}
                disabled={isSaving}
                className="text-xs h-9 hover:bg-surface-soft"
              >
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={isSaving}
                className="bg-accent text-white hover:brightness-110 h-9 px-4 text-xs font-medium rounded-md transition-all flex items-center gap-1.5"
              >
                {isSaving && <Loader2 className="size-3.5 animate-spin" />}
                Validate & Save
              </Button>
            </DialogFooter>
          </form>
        )}
      </DialogContent>
    </Dialog>
  )
}
