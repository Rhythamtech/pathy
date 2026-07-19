'use client'

import { useTheme } from 'next-themes'
import { Toaster as Sonner } from 'sonner'

type ToasterProps = React.ComponentProps<typeof Sonner>

const Toaster = ({ ...props }: ToasterProps) => {
  const { theme = 'system' } = useTheme()

  return (
    <Sonner
      theme={theme as ToasterProps['theme']}
      className="toaster group"
      toastOptions={{
        classNames: {
          toast:
            'group toast group-[.toaster]:bg-canvas group-[.toaster]:text-ink group-[.toaster]:border-hairline group-[.toaster]:shadow-lg',
          description: 'group-[.toast]:text-mute',
          actionButton:
            'group-[.toast]:bg-accent group-[.toast]:text-white',
          cancelButton:
            'group-[.toast]:bg-surface-card group-[.toast]:text-ink'
        }
      }}
      {...props}
    />
  )
}

export { Toaster }
