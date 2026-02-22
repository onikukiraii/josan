import { Outlet, useLocation, Link } from 'react-router-dom'
import { Users, UserX, CalendarDays, TableProperties } from 'lucide-react'
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarInset,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarProvider,
  SidebarTrigger,
} from '@/components/ui/sidebar'
import { Separator } from '@/components/ui/separator'
import type { LucideIcon } from 'lucide-react'

const NAV_ITEMS: { path: string; label: string; icon: LucideIcon }[] = [
  { path: '/members', label: 'メンバー管理', icon: Users },
  { path: '/ng-pairs', label: 'NGペア管理', icon: UserX },
  { path: '/monthly-settings', label: '月次設定', icon: CalendarDays },
  { path: '/shift', label: 'シフト表', icon: TableProperties },
]

export function AppLayout() {
  const location = useLocation()

  return (
    <SidebarProvider>
      <Sidebar>
        <SidebarHeader className="p-4">
          <img src="/logo.svg" alt="Josan" />
        </SidebarHeader>
        <SidebarContent>
          <SidebarGroup>
            <SidebarGroupLabel>メニュー</SidebarGroupLabel>
            <SidebarGroupContent>
              <SidebarMenu>
                {NAV_ITEMS.map((item) => (
                  <SidebarMenuItem key={item.path}>
                    <SidebarMenuButton
                      asChild
                      isActive={location.pathname === item.path}
                    >
                      <Link to={item.path}>
                        <item.icon className="size-4" />
                        <span>{item.label}</span>
                      </Link>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                ))}
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>
        </SidebarContent>
      </Sidebar>
      <SidebarInset>
        <header className="flex h-12 shrink-0 items-center gap-2 border-b px-4">
          <SidebarTrigger className="-ml-1" />
          <Separator orientation="vertical" className="mr-2 h-4" />
          <span className="text-sm font-medium text-muted-foreground">
            {NAV_ITEMS.find((item) => item.path === location.pathname)?.label}
          </span>
        </header>
        <main className="flex-1 p-6 overflow-auto">
          <Outlet />
        </main>
      </SidebarInset>
    </SidebarProvider>
  )
}
