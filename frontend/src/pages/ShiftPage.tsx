import { useState, useEffect, useCallback, useMemo } from 'react'
import { toast } from 'sonner'
import { membersApi, schedulesApi } from '@/api/fetcher'
import type {
  MemberResponse,
  ScheduleResponse,
  ShiftAssignmentResponse,
  ScheduleSummaryResponse,
  MemberSummary,
  UnfulfilledRequest,
  GenerateResponse,
  ShiftType,
} from '@/api/constants'
import { SHIFT_TYPE_LABEL } from '@/api/constants'
import { YearMonthPicker } from '@/components/YearMonthPicker'
import { useYearMonth } from '@/hooks/useYearMonth'
import { Button } from '@/components/ui/button'
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '@/components/ui/table'
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'

const DISPLAY_SHIFT_TYPES: ShiftType[] = [
  'outpatient_leader',
  'treatment_room',
  'beauty',
  'mw_outpatient',
  'outpatient_free',
  'ward_leader',
  'ward',
  'delivery',
  'delivery_charge',
  'ward_free',
  'night_leader',
  'night',
]

const NIGHT_SHIFT_TYPES: ShiftType[] = ['night_leader', 'night']

const SHIFT_TYPE_TO_CAPABILITY: Partial<Record<ShiftType, string>> = {
  outpatient_leader: 'outpatient_leader',
  beauty: 'beauty',
  mw_outpatient: 'mw_outpatient',
  ward_leader: 'ward_leader',
  ward: 'ward_staff',
  night_leader: 'night_leader',
  night: 'night_shift',
  treatment_room: 'day_shift',
  delivery: 'day_shift',
  delivery_charge: 'day_shift',
  ward_free: 'ward_staff',
  outpatient_free: 'day_shift',
}

function getMonthDates(yearMonth: string): Date[] {
  const [y, m] = yearMonth.split('-').map(Number)
  const days = new Date(y, m, 0).getDate()
  return Array.from({ length: days }, (_, i) => new Date(y, m - 1, i + 1))
}

function getDayLabel(date: Date): string {
  return ['日', '月', '火', '水', '木', '金', '土'][date.getDay()]
}

function formatDate(date: Date): string {
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

function buildAssignmentMap(
  assignments: ShiftAssignmentResponse[],
): Map<string, Map<ShiftType, ShiftAssignmentResponse[]>> {
  const map = new Map<string, Map<ShiftType, ShiftAssignmentResponse[]>>()
  for (const a of assignments) {
    if (!map.has(a.date)) {
      map.set(a.date, new Map())
    }
    const dateMap = map.get(a.date)!
    if (!dateMap.has(a.shift_type)) {
      dateMap.set(a.shift_type, [])
    }
    dateMap.get(a.shift_type)!.push(a)
  }
  return map
}

function getFilteredMembers(members: MemberResponse[], shiftType: ShiftType): MemberResponse[] {
  const capability = SHIFT_TYPE_TO_CAPABILITY[shiftType]
  if (!capability) return members
  return members.filter((m) => m.capabilities.includes(capability as MemberResponse['capabilities'][number]))
}

export function ShiftPage() {
  const { yearMonth, setYearMonth } = useYearMonth()
  const [schedule, setSchedule] = useState<ScheduleResponse | null>(null)
  const [members, setMembers] = useState<MemberResponse[]>([])
  const [summary, setSummary] = useState<ScheduleSummaryResponse | null>(null)
  const [unfulfilled, setUnfulfilled] = useState<UnfulfilledRequest[]>([])
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)

  const fetchData = useCallback(async (ym: string) => {
    try {
      setLoading(true)
      const [scheduleData, membersData] = await Promise.all([
        schedulesApi.get(ym),
        membersApi.list(),
      ])
      setMembers(membersData)
      setSchedule(scheduleData)
      setUnfulfilled([])
      if (scheduleData) {
        const summaryData = await schedulesApi.summary(scheduleData.id)
        setSummary(summaryData)
      } else {
        setSummary(null)
      }
    } catch (e) {
      toast.error(e instanceof Error ? e.message : 'データの取得に失敗しました')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchData(yearMonth)
  }, [yearMonth, fetchData])

  const handleGenerate = useCallback(async () => {
    try {
      setGenerating(true)
      const result: GenerateResponse = await schedulesApi.generate({ year_month: yearMonth })
      setSchedule(result.schedule)
      setUnfulfilled(result.unfulfilled_requests)
      if (result.schedule) {
        const summaryData = await schedulesApi.summary(result.schedule.id)
        setSummary(summaryData)
      }
      toast.success('シフトを生成しました')
    } catch (e) {
      toast.error(e instanceof Error ? e.message : 'シフト生成に失敗しました')
    } finally {
      setGenerating(false)
    }
  }, [yearMonth])

  const handlePdfExport = useCallback(() => {
    if (!schedule) return
    window.open(schedulesApi.pdfUrl(schedule.id))
  }, [schedule])

  const handleAssignmentUpdate = useCallback(async (
    assignmentId: number,
    shiftType: ShiftType,
    memberId: number,
  ) => {
    if (!schedule) return
    try {
      const result = await schedulesApi.updateAssignment(schedule.id, assignmentId, {
        shift_type: shiftType,
        member_id: memberId,
      })
      setSchedule((prev) => {
        if (!prev) return prev
        return {
          ...prev,
          assignments: prev.assignments.map((a) =>
            a.id === result.assignment.id ? result.assignment : a,
          ),
        }
      })
      for (const w of result.warnings) {
        toast.warning(w)
      }
      const summaryData = await schedulesApi.summary(schedule.id)
      setSummary(summaryData)
    } catch (e) {
      toast.error(e instanceof Error ? e.message : 'シフトの更新に失敗しました')
    }
  }, [schedule])

  const handleAssignmentDelete = useCallback(async (assignmentId: number) => {
    if (!schedule) return
    try {
      await schedulesApi.deleteAssignment(schedule.id, assignmentId)
      setSchedule((prev) => {
        if (!prev) return prev
        return {
          ...prev,
          assignments: prev.assignments.filter((a) => a.id !== assignmentId),
        }
      })
      const summaryData = await schedulesApi.summary(schedule.id)
      setSummary(summaryData)
    } catch (e) {
      toast.error(e instanceof Error ? e.message : 'シフトの削除に失敗しました')
    }
  }, [schedule])

  const handleAssignmentCreate = useCallback(async (
    dateStr: string,
    shiftType: ShiftType,
    memberId: number,
  ) => {
    if (!schedule) return
    try {
      const result = await schedulesApi.createAssignment(schedule.id, {
        date: dateStr,
        shift_type: shiftType,
        member_id: memberId,
      })
      setSchedule((prev) => {
        if (!prev) return prev
        return {
          ...prev,
          assignments: [...prev.assignments, result.assignment],
        }
      })
      for (const w of result.warnings) {
        toast.warning(w)
      }
      const summaryData = await schedulesApi.summary(schedule.id)
      setSummary(summaryData)
    } catch (e) {
      toast.error(e instanceof Error ? e.message : 'シフトの追加に失敗しました')
    }
  }, [schedule])

  const assignmentMap = useMemo(() => {
    if (!schedule) return new Map<string, Map<ShiftType, ShiftAssignmentResponse[]>>()
    return buildAssignmentMap(schedule.assignments)
  }, [schedule])

  const dates = useMemo(() => getMonthDates(yearMonth), [yearMonth])

  const handleYearMonthChange = useCallback((value: string) => {
    setYearMonth(value)
  }, [setYearMonth])

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-warm-gray-900">
          シフト表
        </h1>
        <p className="text-sm text-warm-gray-400 mt-1">
          生成されたシフトスケジュールの確認・編集を行います
        </p>
      </div>

      <div className="flex items-center gap-3 rounded-2xl border-0 soft-shadow-md bg-white p-4">
        <YearMonthPicker value={yearMonth} onChange={handleYearMonthChange} />
        <div className="flex-1" />
        <Button
          onClick={handleGenerate}
          disabled={generating}
          className="bg-gradient-to-r from-brand-500 to-brand-600 hover:from-brand-600 hover:to-brand-700 shadow-sm"
        >
          {generating ? '生成中...' : '生成'}
        </Button>
        <Button
          variant="outline"
          onClick={handlePdfExport}
          disabled={!schedule}
        >
          PDF出力
        </Button>
      </div>

      {unfulfilled.length > 0 && (
        <Alert>
          <AlertDescription>
            <div className="space-y-2">
              <p className="font-medium text-warm-gray-900">
                充足できなかった希望休があります
              </p>
              <div className="flex flex-wrap gap-2">
                {unfulfilled.map((u, i) => (
                  <Badge key={i} variant="secondary">
                    {u.member_name} - {u.date}
                  </Badge>
                ))}
              </div>
            </div>
          </AlertDescription>
        </Alert>
      )}

      {loading ? (
        <div className="space-y-3">
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-64 w-full" />
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-32 w-full" />
        </div>
      ) : schedule ? (
        <>
          <div className="rounded-2xl border-0 soft-shadow-md bg-white">
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow className="bg-brand-50/60">
                    <TableHead className="sticky left-0 z-10 bg-brand-50/60 font-semibold text-brand-800 min-w-16">
                      日付
                    </TableHead>
                    {DISPLAY_SHIFT_TYPES.map((st) => (
                      <TableHead
                        key={st}
                        className={`font-semibold text-brand-800 text-center min-w-20 ${
                          NIGHT_SHIFT_TYPES.includes(st) ? 'bg-brand-100/40' : ''
                        }`}
                      >
                        {SHIFT_TYPE_LABEL[st]}
                      </TableHead>
                    ))}
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {dates.map((date) => {
                    const dateStr = formatDate(date)
                    const dayOfWeek = date.getDay()
                    const isSunday = dayOfWeek === 0
                    const isSaturday = dayOfWeek === 6
                    const dayAssignments = assignmentMap.get(dateStr)

                    let rowBg = ''
                    if (isSunday) rowBg = 'bg-sunday-bg'
                    else if (isSaturday) rowBg = 'bg-saturday-bg'

                    return (
                      <TableRow key={dateStr} className={rowBg}>
                        <TableCell
                          className={`sticky left-0 z-10 font-medium text-sm whitespace-nowrap ${
                            isSunday
                              ? 'bg-sunday-bg text-sunday'
                              : isSaturday
                                ? 'bg-saturday-bg text-saturday'
                                : 'bg-white text-warm-gray-900'
                          }`}
                        >
                          {date.getDate()} ({getDayLabel(date)})
                        </TableCell>
                        {DISPLAY_SHIFT_TYPES.map((st) => {
                          const cellAssignments = dayAssignments?.get(st) ?? []
                          const isNight = NIGHT_SHIFT_TYPES.includes(st)
                          const filteredMembers = getFilteredMembers(members, st)

                          let cellBg = ''
                          if (isNight) {
                            if (isSunday) cellBg = 'bg-sunday-bg'
                            else if (isSaturday) cellBg = 'bg-saturday-bg'
                            else cellBg = 'bg-brand-50/20'
                          }

                          return (
                            <TableCell
                              key={st}
                              className={`text-center p-1 ${cellBg}`}
                            >
                              <div className="space-y-0.5">
                                {cellAssignments.map((assignment) => (
                                  <DropdownMenu key={assignment.id}>
                                    <DropdownMenuTrigger asChild>
                                      <button
                                        type="button"
                                        className="w-full px-1 py-0.5 rounded text-xs cursor-pointer hover:bg-brand-50 transition-colors text-warm-gray-900 font-medium max-w-16 truncate block mx-auto"
                                      >
                                        {assignment.member_name}
                                      </button>
                                    </DropdownMenuTrigger>
                                    <DropdownMenuContent align="start" className="max-h-64 overflow-y-auto">
                                      <DropdownMenuItem
                                        onClick={() => handleAssignmentDelete(assignment.id)}
                                        className="text-warm-gray-400"
                                      >
                                        割当なし
                                      </DropdownMenuItem>
                                      <DropdownMenuSeparator />
                                      {filteredMembers.map((m) => (
                                        <DropdownMenuItem
                                          key={m.id}
                                          onClick={() => handleAssignmentUpdate(assignment.id, st, m.id)}
                                        >
                                          {m.name}
                                        </DropdownMenuItem>
                                      ))}
                                      {filteredMembers.length === 0 && (
                                        <DropdownMenuItem disabled>
                                          該当メンバーなし
                                        </DropdownMenuItem>
                                      )}
                                    </DropdownMenuContent>
                                  </DropdownMenu>
                                ))}
                                <DropdownMenu>
                                  <DropdownMenuTrigger asChild>
                                    <button
                                      type="button"
                                      className={`w-full px-1 py-0.5 rounded text-xs cursor-pointer hover:bg-brand-50 transition-colors block mx-auto ${
                                        cellAssignments.length > 0
                                          ? 'text-warm-gray-300 hover:text-warm-gray-500'
                                          : 'text-warm-gray-400'
                                      }`}
                                    >
                                      {cellAssignments.length > 0 ? '+' : '—'}
                                    </button>
                                  </DropdownMenuTrigger>
                                  <DropdownMenuContent align="start" className="max-h-64 overflow-y-auto">
                                    {filteredMembers.map((m) => (
                                      <DropdownMenuItem
                                        key={m.id}
                                        onClick={() => handleAssignmentCreate(dateStr, st, m.id)}
                                      >
                                        {m.name}
                                      </DropdownMenuItem>
                                    ))}
                                    {filteredMembers.length === 0 && (
                                      <DropdownMenuItem disabled>
                                        該当メンバーなし
                                      </DropdownMenuItem>
                                    )}
                                  </DropdownMenuContent>
                                </DropdownMenu>
                              </div>
                            </TableCell>
                          )
                        })}
                      </TableRow>
                    )
                  })}
                </TableBody>
              </Table>
            </div>
          </div>

          {summary && (
            <div className="rounded-2xl border-0 soft-shadow-md bg-white">
              <div className="p-4 border-b border-brand-100 bg-brand-50/40">
                <h2 className="text-lg font-semibold text-warm-gray-900">
                  サマリー
                </h2>
                <p className="text-xs text-warm-gray-400 mt-1">
                  基準勤務日数: {summary.expected_working_days}日
                </p>
              </div>
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow className="bg-brand-50/60">
                      <TableHead className="font-semibold text-brand-800">メンバー</TableHead>
                      <TableHead className="font-semibold text-brand-800 text-center">勤務日数</TableHead>
                      <TableHead className="font-semibold text-brand-800 text-center">公休</TableHead>
                      <TableHead className="font-semibold text-brand-800 text-center">夜勤回数</TableHead>
                      <TableHead className="font-semibold text-brand-800 text-center">日祝出勤</TableHead>
                      <TableHead className="font-semibold text-brand-800 text-center">希望休</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {summary.members.map((ms: MemberSummary) => {
                      const isFullTime = ms.employment_type === 'full_time'
                      const workingDaysShort = isFullTime && ms.working_days < summary.expected_working_days
                      const requestUnfulfilled = ms.request_fulfilled < ms.request_total

                      // Build set of day-off dates for this member
                      const dayOffDates = new Set(
                        schedule?.assignments
                          .filter((a) => a.member_id === ms.member_id && a.shift_type === 'day_off')
                          .map((a) => a.date) ?? [],
                      )

                      const hasIssue = workingDaysShort || requestUnfulfilled

                      return (
                        <TableRow
                          key={ms.member_id}
                          className={hasIssue ? 'bg-warning-bg/50 hover:bg-warning-bg/70' : 'hover:bg-brand-50/30'}
                        >
                          <TableCell className="font-medium">
                            <span className={hasIssue ? 'text-warning' : 'text-warm-gray-900'}>
                              {ms.member_name}
                            </span>
                          </TableCell>
                          <TableCell className="text-center">
                            <span className={workingDaysShort ? 'text-warning font-medium' : 'text-warm-gray-700'}>
                              {ms.working_days}
                              {workingDaysShort && (
                                <span className="text-[10px] ml-0.5">
                                  (-{summary.expected_working_days - ms.working_days})
                                </span>
                              )}
                            </span>
                          </TableCell>
                          <TableCell className="text-center text-warm-gray-700">
                            {ms.day_off_count}
                          </TableCell>
                          <TableCell className="text-center text-warm-gray-700">
                            {ms.night_shift_count}
                          </TableCell>
                          <TableCell className="text-center text-warm-gray-700">
                            {ms.holiday_work_count}
                          </TableCell>
                          <TableCell className="text-center">
                            <div>
                              <span className={requestUnfulfilled ? 'text-warning font-medium' : 'text-warm-gray-700'}>
                                {ms.request_fulfilled}/{ms.request_total}
                              </span>
                              {ms.request_dates.length > 0 && (
                                <div className="flex flex-wrap justify-center gap-0.5 mt-0.5">
                                  {ms.request_dates.map((d) => {
                                    const day = Number(d.split('-')[2])
                                    const fulfilled = dayOffDates.has(d)
                                    return (
                                      <span
                                        key={d}
                                        className={`text-[10px] px-1 rounded ${
                                          fulfilled
                                            ? 'bg-brand-50 text-brand-700'
                                            : 'bg-warning-bg text-warning font-medium'
                                        }`}
                                      >
                                        {day}
                                      </span>
                                    )
                                  })}
                                </div>
                              )}
                            </div>
                          </TableCell>
                        </TableRow>
                      )
                    })}
                  </TableBody>
                </Table>
              </div>
            </div>
          )}
        </>
      ) : (
        <div className="rounded-2xl bg-brand-50/30 p-12 text-center animate-in fade-in">
          <p className="text-warm-gray-500">
            シフトが生成されていません。「生成」ボタンを押してシフトを作成してください。
          </p>
        </div>
      )}
    </div>
  )
}
