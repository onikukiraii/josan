import type { components } from './schema'

// --- 型エイリアス ---

export type Qualification = components['schemas']['Qualification']
export type EmploymentType = components['schemas']['EmploymentType']
export type CapabilityType = components['schemas']['CapabilityType']
export type ScheduleStatus = components['schemas']['ScheduleStatus']
export type ShiftType = components['schemas']['ShiftType']

export type MemberResponse = components['schemas']['MemberResponse']
export type NgPairResponse = components['schemas']['NgPairResponse']
export type ShiftRequestResponse = components['schemas']['ShiftRequestResponse']
export type PediatricDoctorScheduleResponse = components['schemas']['PediatricDoctorScheduleResponse']
export type ShiftAssignmentResponse = components['schemas']['ShiftAssignmentResponse']
export type ScheduleResponse = components['schemas']['ScheduleResponse']
export type GenerateResponse = components['schemas']['GenerateResponse']
export type MemberSummary = components['schemas']['MemberSummary']
export type ScheduleSummaryResponse = components['schemas']['ScheduleSummaryResponse']
export type UnfulfilledRequest = components['schemas']['UnfulfilledRequest']

export type MemberCreateParams = components['schemas']['MemberCreateParams']
export type MemberUpdateParams = components['schemas']['MemberUpdateParams']
export type NgPairCreateParams = components['schemas']['NgPairCreateParams']
export type ShiftRequestBulkParams = components['schemas']['ShiftRequestBulkParams']
export type PediatricDoctorScheduleBulkParams = components['schemas']['PediatricDoctorScheduleBulkParams']
export type ScheduleGenerateParams = components['schemas']['ScheduleGenerateParams']
export type ShiftAssignmentUpdateParams = components['schemas']['ShiftAssignmentUpdateParams']

// --- ランタイム用ラベルマップ ---

export const QUALIFICATION_LABEL: Record<Qualification, string> = {
  nurse: '看護師',
  associate_nurse: '准看護師',
  midwife: '助産師',
}

export const EMPLOYMENT_TYPE_LABEL: Record<EmploymentType, string> = {
  full_time: '常勤',
  part_time: '非常勤',
}

export const CAPABILITY_LABEL: Record<CapabilityType, string> = {
  outpatient_leader: '外来リーダー',
  ward_leader: '病棟リーダー',
  night_leader: '夜勤リーダー',
  day_shift: '日勤',
  night_shift: '夜勤',
  beauty: '美容',
  mw_outpatient: '助産師外来',
  ward_staff: '病棟',
  rookie: '新人',
}

export const SHIFT_TYPE_LABEL: Record<ShiftType, string> = {
  outpatient_leader: '外来L',
  treatment_room: '処置室',
  beauty: '美容',
  mw_outpatient: '助外',
  ward_leader: '病棟L',
  ward: '病棟',
  delivery: '分娩',
  delivery_charge: '分担',
  night_leader: '夜L',
  night: '夜勤',
  day_off: '公休',
}
