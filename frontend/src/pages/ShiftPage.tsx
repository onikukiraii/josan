import { useState, useEffect, useCallback, useMemo } from 'react'
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
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'

const DISPLAY_SHIFT_TYPES: ShiftType[] = [
  'outpatient_leader',
  'treatment_room',
  'beauty',
  'mw_outpatient',
  'ward_leader',
  'ward',
  'delivery',
  'delivery_charge',
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
  const [error, setError] = useState<string | null>(null)

  const fetchData = useCallback(async (ym: string) => {
    try {
      setLoading(true)
      setError(null)
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
      setError(e instanceof Error ? e.message : 'データの取得に失敗しました')
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
      setError(null)
      const result: GenerateResponse = await schedulesApi.generate({ year_month: yearMonth })
      setSchedule(result.schedule)
      setUnfulfilled(result.unfulfilled_requests)
      if (result.schedule) {
        const summaryData = await schedulesApi.summary(result.schedule.id)
        setSummary(summaryData)
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'シフト生成に失敗しました')
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
      setError(null)
      const updated = await schedulesApi.updateAssignment(schedule.id, assignmentId, {
        shift_type: shiftType,
        member_id: memberId,
      })
      setSchedule((prev) => {
        if (!prev) return prev
        return {
          ...prev,
          assignments: prev.assignments.map((a) =>
            a.id === updated.id ? updated : a,
          ),
        }
      })
      const summaryData = await schedulesApi.summary(schedule.id)
      setSummary(summaryData)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'シフトの更新に失敗しました')
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
        <p className="text-sm text-warm-gray-500 mt-1">
          生成されたシフトスケジュールの確認・編集を行います
        </p>
      </div>

      <div className="flex items-center gap-3 rounded-lg border border-warm-gray-200 bg-white p-4">
        <YearMonthPicker value={yearMonth} onChange={handleYearMonthChange} />
        <div className="flex-1" />
        <Button
          onClick={handleGenerate}
          disabled={generating}
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

      {error && (
        <Alert variant="destructive">
          <AlertDescription className="whitespace-pre-line">{error}</AlertDescription>
        </Alert>
      )}

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
          <div className="rounded-lg border border-warm-gray-200 bg-white">
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow className="bg-warm-gray-50">
                    <TableHead className="sticky left-0 z-10 bg-warm-gray-50 font-semibold text-warm-gray-700 min-w-16">
                      日付
                    </TableHead>
                    {DISPLAY_SHIFT_TYPES.map((st) => (
                      <TableHead
                        key={st}
                        className={`font-semibold text-warm-gray-700 text-center min-w-20 ${
                          NIGHT_SHIFT_TYPES.includes(st) ? 'bg-warm-gray-200' : ''
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
                            else cellBg = 'bg-warm-gray-100'
                          }

                          return (
                            <TableCell
                              key={st}
                              className={`text-center p-1 ${cellBg}`}
                            >
                              {cellAssignments.length > 0 ? (
                                <div className="space-y-0.5">
                                  {cellAssignments.map((assignment) => (
                                    <DropdownMenu key={assignment.id}>
                                      <DropdownMenuTrigger asChild>
                                        <button
                                          type="button"
                                          className="w-full px-1 py-0.5 rounded text-xs cursor-pointer hover:bg-warm-gray-200/60 transition-colors text-warm-gray-900 font-medium max-w-16 truncate block mx-auto"
                                        >
                                          {assignment.member_name}
                                        </button>
                                      </DropdownMenuTrigger>
                                      <DropdownMenuContent align="start" className="max-h-64 overflow-y-auto">
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
                                </div>
                              ) : (
                                <span className="text-xs text-warm-gray-400">—</span>
                              )}
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
            <div className="rounded-lg border border-warm-gray-200 bg-white">
              <div className="p-4 border-b border-warm-gray-200 bg-warm-gray-50">
                <h2 className="text-lg font-semibold text-warm-gray-900">
                  サマリー
                </h2>
              </div>
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow className="bg-warm-gray-50">
                      <TableHead className="font-semibold text-warm-gray-700">メンバー</TableHead>
                      <TableHead className="font-semibold text-warm-gray-700 text-center">勤務日数</TableHead>
                      <TableHead className="font-semibold text-warm-gray-700 text-center">公休</TableHead>
                      <TableHead className="font-semibold text-warm-gray-700 text-center">夜勤回数</TableHead>
                      <TableHead className="font-semibold text-warm-gray-700 text-center">日祝出勤</TableHead>
                      <TableHead className="font-semibold text-warm-gray-700 text-center">希望休</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {summary.members.map((ms: MemberSummary) => (
                      <TableRow key={ms.member_id}>
                        <TableCell className="font-medium text-warm-gray-900">
                          {ms.member_name}
                        </TableCell>
                        <TableCell className="text-center text-warm-gray-700">
                          {ms.working_days}
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
                        <TableCell className="text-center text-warm-gray-700">
                          <span className={ms.request_fulfilled < ms.request_total ? 'text-warning font-medium' : ''}>
                            {ms.request_fulfilled}/{ms.request_total}
                          </span>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </div>
          )}
        </>
      ) : (
        <div className="rounded-lg border border-warm-gray-200 bg-white p-12 text-center">
          <p className="text-warm-gray-500">
            シフトが生成されていません。「生成」ボタンを押してシフトを作成してください。
          </p>
        </div>
      )}
    </div>
  )
}
