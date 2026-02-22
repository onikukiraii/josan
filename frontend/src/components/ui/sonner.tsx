import {
  CircleCheckIcon,
  InfoIcon,
  Loader2Icon,
  OctagonXIcon,
  TriangleAlertIcon,
} from "lucide-react"
import { Toaster as Sonner, type ToasterProps } from "sonner"

const Toaster = ({ ...props }: ToasterProps) => {
  return (
    <Sonner
      theme="light"
      position="top-right"
      visibleToasts={1}
      className="toaster group"
      icons={{
        success: <CircleCheckIcon className="size-4" />,
        info: <InfoIcon className="size-4" />,
        warning: <TriangleAlertIcon className="size-4" />,
        error: <OctagonXIcon className="size-4" />,
        loading: <Loader2Icon className="size-4 animate-spin" />,
      }}
      style={
        {
          "--normal-bg": "var(--popover)",
          "--normal-text": "var(--popover-foreground)",
          "--normal-border": "var(--border)",
          "--success-bg": "var(--color-success-bg)",
          "--success-text": "var(--color-success)",
          "--success-border": "var(--color-success-bg)",
          "--error-bg": "var(--color-error-bg)",
          "--error-text": "var(--color-error)",
          "--error-border": "var(--color-error-bg)",
          "--warning-bg": "var(--color-warning-bg)",
          "--warning-text": "var(--color-warning)",
          "--warning-border": "var(--color-warning-bg)",
          "--info-bg": "var(--color-info-bg)",
          "--info-text": "var(--color-info)",
          "--info-border": "var(--color-info-bg)",
          "--border-radius": "var(--radius)",
        } as React.CSSProperties
      }
      {...props}
    />
  )
}

export { Toaster }
