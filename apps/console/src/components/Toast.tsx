import { useState, useCallback } from 'react'

interface Toast {
  id: number
  message: string
  type: 'success' | 'error' | 'info'
}

let toastId = 0
let globalShowToast: ((message: string, type: 'success' | 'error' | 'info') => void) | null = null

export function showToast(message: string, type: 'success' | 'error' | 'info' = 'info') {
  if (globalShowToast) {
    globalShowToast(message, type)
  } else {
    // Fallback to alert if ToastProvider is not mounted
    alert(message)
  }
}

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([])

  const handleShowToast = useCallback((message: string, type: 'success' | 'error' | 'info') => {
    const id = ++toastId
    setToasts(prev => [...prev, { id, message, type }])
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id))
    }, 3000)
  }, [])

  // Register global handler
  if (globalShowToast !== handleShowToast) {
    globalShowToast = handleShowToast
  }

  const colors = {
    success: { bg: '#f6ffed', border: '#b7eb8f', text: '#52c41a' },
    error: { bg: '#fff2f0', border: '#ffccc7', text: '#ff4d4f' },
    info: { bg: '#e6f4ff', border: '#91caff', text: '#1677ff' },
  }

  return (
    <>
      {children}
      <div style={{
        position: 'fixed',
        top: 16,
        right: 16,
        zIndex: 9999,
        display: 'flex',
        flexDirection: 'column',
        gap: 8,
      }}>
        {toasts.map(toast => (
          <div
            key={toast.id}
            onClick={() => setToasts(prev => prev.filter(t => t.id !== toast.id))}
            style={{
              padding: '12px 16px',
              borderRadius: 4,
              background: colors[toast.type].bg,
              border: `1px solid ${colors[toast.type].border}`,
              color: colors[toast.type].text,
              fontSize: 14,
              cursor: 'pointer',
              minWidth: 250,
              maxWidth: 400,
              boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
            }}
          >
            {toast.message}
          </div>
        ))}
      </div>
    </>
  )
}
