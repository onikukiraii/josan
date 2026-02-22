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
        <SidebarHeader className="p-6">
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
                      className={location.pathname === item.path ? 'bg-brand-100 text-brand-800 font-semibold border-l-3 border-brand-500' : 'hover:bg-brand-100 hover:text-brand-700'}
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
        <header className="flex h-12 shrink-0 items-center gap-2 px-4 bg-white/80 backdrop-blur-sm soft-shadow">
          <SidebarTrigger className="-ml-1" />
          <Separator orientation="vertical" className="mr-2 h-4" />
          <span className="text-sm font-medium text-muted-foreground">
            {NAV_ITEMS.find((item) => item.path === location.pathname)?.label}
          </span>
        </header>
        <main className="flex-1 p-8 overflow-auto">
          <Outlet />
        </main>
      </SidebarInset>
    </SidebarProvider>
  )
}
