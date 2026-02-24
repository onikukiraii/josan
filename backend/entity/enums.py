import enum


class Qualification(str, enum.Enum):
    nurse = "nurse"
    associate_nurse = "associate_nurse"
    midwife = "midwife"

    @property
    def label(self) -> str:
        labels = {"nurse": "看護師", "associate_nurse": "准看護師", "midwife": "助産師"}
        return labels[self.value]


class EmploymentType(str, enum.Enum):
    full_time = "full_time"
    part_time = "part_time"

    @property
    def label(self) -> str:
        labels = {"full_time": "常勤", "part_time": "非常勤"}
        return labels[self.value]


class CapabilityType(str, enum.Enum):
    outpatient_leader = "outpatient_leader"
    ward_leader = "ward_leader"
    night_leader = "night_leader"
    day_shift = "day_shift"
    night_shift = "night_shift"
    beauty = "beauty"
    mw_outpatient = "mw_outpatient"
    ward_staff = "ward_staff"
    rookie = "rookie"
    early_shift = "early_shift"

    @property
    def label(self) -> str:
        labels = {
            "outpatient_leader": "外来リーダー",
            "ward_leader": "病棟リーダー",
            "night_leader": "夜勤リーダー",
            "day_shift": "日勤",
            "night_shift": "夜勤",
            "beauty": "美容",
            "mw_outpatient": "助産師外来",
            "ward_staff": "病棟",
            "rookie": "新人",
            "early_shift": "早番",
        }
        return labels[self.value]


class ScheduleStatus(str, enum.Enum):
    draft = "draft"
    published = "published"

    @property
    def label(self) -> str:
        labels = {"draft": "下書き", "published": "公開"}
        return labels[self.value]


class ShiftType(str, enum.Enum):
    outpatient_leader = "outpatient_leader"
    treatment_room = "treatment_room"
    beauty = "beauty"
    mw_outpatient = "mw_outpatient"
    ward_leader = "ward_leader"
    ward = "ward"
    delivery = "delivery"
    delivery_charge = "delivery_charge"
    ward_free = "ward_free"
    outpatient_free = "outpatient_free"
    night_leader = "night_leader"
    night = "night"
    day_off = "day_off"
    paid_leave = "paid_leave"

    @property
    def label(self) -> str:
        labels = {
            "outpatient_leader": "外来L",
            "treatment_room": "処置室",
            "beauty": "美容",
            "mw_outpatient": "助外",
            "ward_leader": "病棟L",
            "ward": "病棟",
            "delivery": "分娩",
            "delivery_charge": "分担",
            "ward_free": "病棟F",
            "outpatient_free": "外来F",
            "night_leader": "夜L",
            "night": "夜勤",
            "day_off": "公休",
            "paid_leave": "有給",
        }
        return labels[self.value]


class RequestType(str, enum.Enum):
    day_off = "day_off"
    paid_leave = "paid_leave"
    day_shift_request = "day_shift_request"
