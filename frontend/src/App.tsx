import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AppLayout } from '@/layouts/AppLayout'
import { MemberPage } from '@/pages/MemberPage'
import { NgPairPage } from '@/pages/NgPairPage'
import { MonthlySettingsPage } from '@/pages/MonthlySettingsPage'
import { ShiftPage } from '@/pages/ShiftPage'
import { Toaster } from '@/components/ui/sonner'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppLayout />}>
          <Route path="/" element={<Navigate to="/members" replace />} />
          <Route path="/members" element={<MemberPage />} />
          <Route path="/ng-pairs" element={<NgPairPage />} />
          <Route path="/monthly-settings" element={<MonthlySettingsPage />} />
          <Route path="/shift" element={<ShiftPage />} />
        </Route>
      </Routes>
      <Toaster />
    </BrowserRouter>
  )
}

export default App
