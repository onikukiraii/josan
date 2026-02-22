import createClient from 'openapi-fetch'
import type { paths } from './schema'
import type {
  MemberResponse,
  MemberCreateParams,
  MemberUpdateParams,
  NgPairResponse,
  NgPairCreateParams,
  ShiftRequestResponse,
  ShiftRequestBulkParams,
  PediatricDoctorScheduleResponse,
  PediatricDoctorScheduleBulkParams,
  ScheduleResponse,
  GenerateResponse,
  ShiftAssignmentResponse,
  ShiftAssignmentUpdateParams,
  ScheduleSummaryResponse,
  ScheduleGenerateParams,
} from './constants'

const BASE_URL = 'http://localhost:8000'

const api = createClient<paths>({ baseUrl: BASE_URL })

function unwrap<T>(result: { data?: T; error?: unknown }): T {
  if (result.error !== undefined) {
    throw new Error(`API error: ${JSON.stringify(result.error)}`)
  }
  return result.data as T
}

// --- Members ---

export const membersApi = {
  list: async () => {
    const res = await api.GET('/members/')
    return unwrap<MemberResponse[]>(res)
  },
  get: async (id: number) => {
    const res = await api.GET('/members/{member_id}', {
      params: { path: { member_id: id } },
    })
    return unwrap<MemberResponse>(res)
  },
  create: async (params: MemberCreateParams) => {
    const res = await api.POST('/members/', {
      body: params,
    })
    return unwrap<MemberResponse>(res)
  },
  update: async (id: number, params: MemberUpdateParams) => {
    const res = await api.PUT('/members/{member_id}', {
      params: { path: { member_id: id } },
      body: params,
    })
    return unwrap<MemberResponse>(res)
  },
  delete: async (id: number) => {
    const res = await api.DELETE('/members/{member_id}', {
      params: { path: { member_id: id } },
    })
    unwrap(res)
  },
}

// --- NG Pairs ---

export const ngPairsApi = {
  list: async () => {
    const res = await api.GET('/ng-pairs/')
    return unwrap<NgPairResponse[]>(res)
  },
  create: async (params: NgPairCreateParams) => {
    const res = await api.POST('/ng-pairs/', {
      body: params,
    })
    return unwrap<NgPairResponse>(res)
  },
  delete: async (id: number) => {
    const res = await api.DELETE('/ng-pairs/{ng_pair_id}', {
      params: { path: { ng_pair_id: id } },
    })
    unwrap(res)
  },
}

// --- Shift Requests ---

export const shiftRequestsApi = {
  list: async (yearMonth: string) => {
    const res = await api.GET('/shift-requests/', {
      params: { query: { year_month: yearMonth } },
    })
    return unwrap<ShiftRequestResponse[]>(res)
  },
  bulkUpdate: async (params: ShiftRequestBulkParams) => {
    const res = await api.PUT('/shift-requests/', {
      body: params,
    })
    return unwrap<ShiftRequestResponse[]>(res)
  },
}

// --- Pediatric Doctor Schedules ---

export const pediatricApi = {
  list: async (yearMonth: string) => {
    const res = await api.GET('/pediatric-doctor-schedules/', {
      params: { query: { year_month: yearMonth } },
    })
    return unwrap<PediatricDoctorScheduleResponse[]>(res)
  },
  bulkUpdate: async (params: PediatricDoctorScheduleBulkParams) => {
    const res = await api.PUT('/pediatric-doctor-schedules/', {
      body: params,
    })
    return unwrap<PediatricDoctorScheduleResponse[]>(res)
  },
}

// --- Schedules ---

export const schedulesApi = {
  get: async (yearMonth: string) => {
    const res = await api.GET('/schedules/', {
      params: { query: { year_month: yearMonth } },
    })
    return unwrap<ScheduleResponse | null>(res)
  },
  generate: async (params: ScheduleGenerateParams) => {
    const res = await api.POST('/schedules/generate', {
      body: params,
    })
    return unwrap<GenerateResponse>(res)
  },
  updateAssignment: async (
    scheduleId: number,
    assignmentId: number,
    params: ShiftAssignmentUpdateParams,
  ) => {
    const res = await api.PUT(
      '/schedules/{schedule_id}/assignments/{assignment_id}',
      {
        params: { path: { schedule_id: scheduleId, assignment_id: assignmentId } },
        body: params,
      },
    )
    return unwrap<ShiftAssignmentResponse>(res)
  },
  summary: async (scheduleId: number) => {
    const res = await api.GET('/schedules/{schedule_id}/summary', {
      params: { path: { schedule_id: scheduleId } },
    })
    return unwrap<ScheduleSummaryResponse>(res)
  },
  pdfUrl: (scheduleId: number) =>
    `${BASE_URL}/schedules/${scheduleId}/pdf`,
}
