"""
Case Management Order (CMO) Tracker

Tracks Case Management Orders and their deadlines in California civil cases.
CMOs set the schedule and deadlines for the case including discovery cutoffs,
motion deadlines, and trial dates.
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional, List, Dict
from uuid import uuid4

from ..models.case import Case
from ..models.deadline import Deadline, DeadlineType, DeadlinePriority, DeadlineStatus
from ..models.event import CourtEvent, EventType
from .deadline_calculator import DeadlineCalculator


@dataclass
class CMODeadline:
    """A deadline specified in a Case Management Order."""
    name: str
    due_date: date
    description: str = ""
    deadline_type: DeadlineType = DeadlineType.CMO_DEADLINE
    is_completed: bool = False
    completed_date: Optional[date] = None
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            'name': self.name,
            'due_date': self.due_date.isoformat(),
            'description': self.description,
            'deadline_type': self.deadline_type.value,
            'is_completed': self.is_completed,
            'completed_date': self.completed_date.isoformat() if self.completed_date else None,
            'notes': self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'CMODeadline':
        return cls(
            name=data['name'],
            due_date=date.fromisoformat(data['due_date']),
            description=data.get('description', ''),
            deadline_type=DeadlineType(data.get('deadline_type', 'cmo_deadline')),
            is_completed=data.get('is_completed', False),
            completed_date=date.fromisoformat(data['completed_date']) if data.get('completed_date') else None,
            notes=data.get('notes', ''),
        )


@dataclass
class CaseManagementOrder:
    """
    Represents a Case Management Order in a California civil case.

    CMOs typically include:
    - Trial date
    - Discovery cutoffs (fact and expert)
    - Motion deadlines
    - Expert designation deadlines
    - CMC and FSC dates
    """
    case_id: str
    order_date: date

    id: str = field(default_factory=lambda: str(uuid4()))
    order_number: Optional[str] = None
    judge_name: Optional[str] = None
    department: Optional[str] = None

    # Key dates from CMO
    trial_date: Optional[date] = None
    fsc_date: Optional[date] = None  # Final Status Conference
    next_cmc_date: Optional[date] = None

    # Discovery deadlines
    fact_discovery_cutoff: Optional[date] = None
    expert_discovery_cutoff: Optional[date] = None
    expert_designation_plaintiff: Optional[date] = None
    expert_designation_defendant: Optional[date] = None
    expert_deposition_cutoff: Optional[date] = None

    # Motion deadlines
    law_and_motion_cutoff: Optional[date] = None
    msj_filing_cutoff: Optional[date] = None
    msj_hearing_cutoff: Optional[date] = None
    motions_in_limine_cutoff: Optional[date] = None

    # Trial preparation deadlines
    jury_instructions_due: Optional[date] = None
    exhibit_list_due: Optional[date] = None
    witness_list_due: Optional[date] = None
    trial_brief_due: Optional[date] = None
    proposed_statement_of_decision: Optional[date] = None

    # ADR deadlines
    mediation_deadline: Optional[date] = None
    mandatory_settlement_conference: Optional[date] = None

    # Custom deadlines from CMO
    custom_deadlines: List[CMODeadline] = field(default_factory=list)

    # Status
    is_superseded: bool = False
    superseded_by_id: Optional[str] = None
    superseded_date: Optional[date] = None

    # Metadata
    document_id: Optional[str] = None  # Link to Document object
    roa_entry_number: Optional[str] = None
    notes: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def add_custom_deadline(self, name: str, due_date: date,
                            description: str = "",
                            deadline_type: DeadlineType = DeadlineType.CMO_DEADLINE) -> CMODeadline:
        """Add a custom deadline from the CMO."""
        deadline = CMODeadline(
            name=name,
            due_date=due_date,
            description=description,
            deadline_type=deadline_type
        )
        self.custom_deadlines.append(deadline)
        self.updated_at = datetime.now()
        return deadline

    def mark_superseded(self, new_cmo_id: str) -> None:
        """Mark this CMO as superseded by a newer one."""
        self.is_superseded = True
        self.superseded_by_id = new_cmo_id
        self.superseded_date = date.today()
        self.updated_at = datetime.now()

    def get_all_deadlines(self) -> List[tuple]:
        """Get all deadlines from this CMO as list of (name, date) tuples."""
        deadlines = []

        # Standard deadlines
        if self.trial_date:
            deadlines.append(('Trial', self.trial_date))
        if self.fsc_date:
            deadlines.append(('Final Status Conference', self.fsc_date))
        if self.next_cmc_date:
            deadlines.append(('Case Management Conference', self.next_cmc_date))
        if self.fact_discovery_cutoff:
            deadlines.append(('Fact Discovery Cutoff', self.fact_discovery_cutoff))
        if self.expert_discovery_cutoff:
            deadlines.append(('Expert Discovery Cutoff', self.expert_discovery_cutoff))
        if self.expert_designation_plaintiff:
            deadlines.append(('Expert Designation (Plaintiff)', self.expert_designation_plaintiff))
        if self.expert_designation_defendant:
            deadlines.append(('Expert Designation (Defendant)', self.expert_designation_defendant))
        if self.expert_deposition_cutoff:
            deadlines.append(('Expert Deposition Cutoff', self.expert_deposition_cutoff))
        if self.law_and_motion_cutoff:
            deadlines.append(('Law & Motion Cutoff', self.law_and_motion_cutoff))
        if self.msj_filing_cutoff:
            deadlines.append(('MSJ Filing Cutoff', self.msj_filing_cutoff))
        if self.msj_hearing_cutoff:
            deadlines.append(('MSJ Hearing Cutoff', self.msj_hearing_cutoff))
        if self.motions_in_limine_cutoff:
            deadlines.append(('Motions in Limine Cutoff', self.motions_in_limine_cutoff))
        if self.jury_instructions_due:
            deadlines.append(('Jury Instructions Due', self.jury_instructions_due))
        if self.exhibit_list_due:
            deadlines.append(('Exhibit List Due', self.exhibit_list_due))
        if self.witness_list_due:
            deadlines.append(('Witness List Due', self.witness_list_due))
        if self.trial_brief_due:
            deadlines.append(('Trial Brief Due', self.trial_brief_due))
        if self.mediation_deadline:
            deadlines.append(('Mediation', self.mediation_deadline))
        if self.mandatory_settlement_conference:
            deadlines.append(('Mandatory Settlement Conference', self.mandatory_settlement_conference))

        # Custom deadlines
        for custom in self.custom_deadlines:
            if not custom.is_completed:
                deadlines.append((custom.name, custom.due_date))

        # Sort by date
        deadlines.sort(key=lambda x: x[1])
        return deadlines

    def get_upcoming_deadlines(self, days_ahead: int = 30) -> List[tuple]:
        """Get deadlines coming up in the next N days."""
        today = date.today()
        cutoff = today + datetime.timedelta(days=days_ahead) if hasattr(datetime, 'timedelta') else date(today.year, today.month, today.day)
        from datetime import timedelta
        cutoff = today + timedelta(days=days_ahead)

        all_deadlines = self.get_all_deadlines()
        return [(name, d) for name, d in all_deadlines if today <= d <= cutoff]

    def get_past_due_deadlines(self) -> List[tuple]:
        """Get deadlines that have passed."""
        today = date.today()
        all_deadlines = self.get_all_deadlines()
        return [(name, d) for name, d in all_deadlines if d < today]

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'case_id': self.case_id,
            'order_date': self.order_date.isoformat(),
            'order_number': self.order_number,
            'judge_name': self.judge_name,
            'department': self.department,
            'trial_date': self.trial_date.isoformat() if self.trial_date else None,
            'fsc_date': self.fsc_date.isoformat() if self.fsc_date else None,
            'next_cmc_date': self.next_cmc_date.isoformat() if self.next_cmc_date else None,
            'fact_discovery_cutoff': self.fact_discovery_cutoff.isoformat() if self.fact_discovery_cutoff else None,
            'expert_discovery_cutoff': self.expert_discovery_cutoff.isoformat() if self.expert_discovery_cutoff else None,
            'expert_designation_plaintiff': self.expert_designation_plaintiff.isoformat() if self.expert_designation_plaintiff else None,
            'expert_designation_defendant': self.expert_designation_defendant.isoformat() if self.expert_designation_defendant else None,
            'expert_deposition_cutoff': self.expert_deposition_cutoff.isoformat() if self.expert_deposition_cutoff else None,
            'law_and_motion_cutoff': self.law_and_motion_cutoff.isoformat() if self.law_and_motion_cutoff else None,
            'msj_filing_cutoff': self.msj_filing_cutoff.isoformat() if self.msj_filing_cutoff else None,
            'msj_hearing_cutoff': self.msj_hearing_cutoff.isoformat() if self.msj_hearing_cutoff else None,
            'motions_in_limine_cutoff': self.motions_in_limine_cutoff.isoformat() if self.motions_in_limine_cutoff else None,
            'jury_instructions_due': self.jury_instructions_due.isoformat() if self.jury_instructions_due else None,
            'exhibit_list_due': self.exhibit_list_due.isoformat() if self.exhibit_list_due else None,
            'witness_list_due': self.witness_list_due.isoformat() if self.witness_list_due else None,
            'trial_brief_due': self.trial_brief_due.isoformat() if self.trial_brief_due else None,
            'proposed_statement_of_decision': self.proposed_statement_of_decision.isoformat() if self.proposed_statement_of_decision else None,
            'mediation_deadline': self.mediation_deadline.isoformat() if self.mediation_deadline else None,
            'mandatory_settlement_conference': self.mandatory_settlement_conference.isoformat() if self.mandatory_settlement_conference else None,
            'custom_deadlines': [d.to_dict() for d in self.custom_deadlines],
            'is_superseded': self.is_superseded,
            'superseded_by_id': self.superseded_by_id,
            'superseded_date': self.superseded_date.isoformat() if self.superseded_date else None,
            'document_id': self.document_id,
            'roa_entry_number': self.roa_entry_number,
            'notes': self.notes,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'CaseManagementOrder':
        custom_deadlines = [CMODeadline.from_dict(d) for d in data.get('custom_deadlines', [])]
        return cls(
            id=data.get('id', str(uuid4())),
            case_id=data['case_id'],
            order_date=date.fromisoformat(data['order_date']),
            order_number=data.get('order_number'),
            judge_name=data.get('judge_name'),
            department=data.get('department'),
            trial_date=date.fromisoformat(data['trial_date']) if data.get('trial_date') else None,
            fsc_date=date.fromisoformat(data['fsc_date']) if data.get('fsc_date') else None,
            next_cmc_date=date.fromisoformat(data['next_cmc_date']) if data.get('next_cmc_date') else None,
            fact_discovery_cutoff=date.fromisoformat(data['fact_discovery_cutoff']) if data.get('fact_discovery_cutoff') else None,
            expert_discovery_cutoff=date.fromisoformat(data['expert_discovery_cutoff']) if data.get('expert_discovery_cutoff') else None,
            expert_designation_plaintiff=date.fromisoformat(data['expert_designation_plaintiff']) if data.get('expert_designation_plaintiff') else None,
            expert_designation_defendant=date.fromisoformat(data['expert_designation_defendant']) if data.get('expert_designation_defendant') else None,
            expert_deposition_cutoff=date.fromisoformat(data['expert_deposition_cutoff']) if data.get('expert_deposition_cutoff') else None,
            law_and_motion_cutoff=date.fromisoformat(data['law_and_motion_cutoff']) if data.get('law_and_motion_cutoff') else None,
            msj_filing_cutoff=date.fromisoformat(data['msj_filing_cutoff']) if data.get('msj_filing_cutoff') else None,
            msj_hearing_cutoff=date.fromisoformat(data['msj_hearing_cutoff']) if data.get('msj_hearing_cutoff') else None,
            motions_in_limine_cutoff=date.fromisoformat(data['motions_in_limine_cutoff']) if data.get('motions_in_limine_cutoff') else None,
            jury_instructions_due=date.fromisoformat(data['jury_instructions_due']) if data.get('jury_instructions_due') else None,
            exhibit_list_due=date.fromisoformat(data['exhibit_list_due']) if data.get('exhibit_list_due') else None,
            witness_list_due=date.fromisoformat(data['witness_list_due']) if data.get('witness_list_due') else None,
            trial_brief_due=date.fromisoformat(data['trial_brief_due']) if data.get('trial_brief_due') else None,
            proposed_statement_of_decision=date.fromisoformat(data['proposed_statement_of_decision']) if data.get('proposed_statement_of_decision') else None,
            mediation_deadline=date.fromisoformat(data['mediation_deadline']) if data.get('mediation_deadline') else None,
            mandatory_settlement_conference=date.fromisoformat(data['mandatory_settlement_conference']) if data.get('mandatory_settlement_conference') else None,
            custom_deadlines=custom_deadlines,
            is_superseded=data.get('is_superseded', False),
            superseded_by_id=data.get('superseded_by_id'),
            superseded_date=date.fromisoformat(data['superseded_date']) if data.get('superseded_date') else None,
            document_id=data.get('document_id'),
            roa_entry_number=data.get('roa_entry_number'),
            notes=data.get('notes', ''),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.now(),
            updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else datetime.now(),
        )


class CMOTracker:
    """
    Manages Case Management Orders for California court cases.

    Provides functionality to:
    - Track multiple CMOs per case
    - Auto-generate deadlines from CMO dates
    - Track when CMOs are superseded
    - Generate deadline reports
    """

    def __init__(self):
        """Initialize the CMO tracker."""
        self.cmos: Dict[str, CaseManagementOrder] = {}  # cmo_id -> CMO
        self.case_cmos: Dict[str, List[str]] = {}  # case_id -> [cmo_ids]
        self.deadline_calculator = DeadlineCalculator()

    def add_cmo(self, cmo: CaseManagementOrder) -> CaseManagementOrder:
        """Add a new CMO."""
        # Mark previous CMOs as superseded
        if cmo.case_id in self.case_cmos:
            for prev_cmo_id in self.case_cmos[cmo.case_id]:
                prev_cmo = self.cmos.get(prev_cmo_id)
                if prev_cmo and not prev_cmo.is_superseded:
                    prev_cmo.mark_superseded(cmo.id)

        self.cmos[cmo.id] = cmo

        if cmo.case_id not in self.case_cmos:
            self.case_cmos[cmo.case_id] = []
        self.case_cmos[cmo.case_id].append(cmo.id)

        return cmo

    def create_cmo(self, case_id: str, order_date: date, **kwargs) -> CaseManagementOrder:
        """Create and add a new CMO."""
        cmo = CaseManagementOrder(case_id=case_id, order_date=order_date, **kwargs)
        return self.add_cmo(cmo)

    def get_cmo(self, cmo_id: str) -> Optional[CaseManagementOrder]:
        """Get a CMO by ID."""
        return self.cmos.get(cmo_id)

    def get_current_cmo(self, case_id: str) -> Optional[CaseManagementOrder]:
        """Get the current (non-superseded) CMO for a case."""
        for cmo_id in reversed(self.case_cmos.get(case_id, [])):
            cmo = self.cmos.get(cmo_id)
            if cmo and not cmo.is_superseded:
                return cmo
        return None

    def get_case_cmos(self, case_id: str, include_superseded: bool = False) -> List[CaseManagementOrder]:
        """Get all CMOs for a case."""
        cmo_ids = self.case_cmos.get(case_id, [])
        cmos = [self.cmos[cid] for cid in cmo_ids if cid in self.cmos]

        if not include_superseded:
            cmos = [c for c in cmos if not c.is_superseded]

        return sorted(cmos, key=lambda c: c.order_date, reverse=True)

    def generate_deadlines_from_cmo(self, cmo: CaseManagementOrder) -> List[Deadline]:
        """
        Generate Deadline objects from a CMO.

        Creates deadline objects for all dates specified in the CMO.
        """
        deadlines = []

        # Trial date
        if cmo.trial_date:
            deadlines.append(Deadline(
                title="Trial",
                deadline_type=DeadlineType.CMO_DEADLINE,
                due_date=cmo.trial_date,
                case_id=cmo.case_id,
                priority=DeadlinePriority.CRITICAL,
                crc_rule="CRC 3.720",
                notes="Trial date per Case Management Order"
            ))

        # Final Status Conference
        if cmo.fsc_date:
            deadlines.append(Deadline(
                title="Final Status Conference",
                deadline_type=DeadlineType.CMO_DEADLINE,
                due_date=cmo.fsc_date,
                case_id=cmo.case_id,
                priority=DeadlinePriority.HIGH,
                notes="FSC per Case Management Order"
            ))

        # Fact Discovery Cutoff
        if cmo.fact_discovery_cutoff:
            deadlines.append(Deadline(
                title="Fact Discovery Cutoff",
                deadline_type=DeadlineType.FACT_DISCOVERY_CUTOFF,
                due_date=cmo.fact_discovery_cutoff,
                case_id=cmo.case_id,
                priority=DeadlinePriority.HIGH,
                notes="Last day to complete fact discovery"
            ))

        # Expert Discovery Cutoff
        if cmo.expert_discovery_cutoff:
            deadlines.append(Deadline(
                title="Expert Discovery Cutoff",
                deadline_type=DeadlineType.EXPERT_DISCOVERY_CUTOFF,
                due_date=cmo.expert_discovery_cutoff,
                case_id=cmo.case_id,
                priority=DeadlinePriority.HIGH,
                notes="Last day to complete expert discovery"
            ))

        # Expert Designations
        if cmo.expert_designation_plaintiff:
            deadlines.append(Deadline(
                title="Expert Designation (Plaintiff)",
                deadline_type=DeadlineType.EXPERT_DESIGNATION_DUE,
                due_date=cmo.expert_designation_plaintiff,
                case_id=cmo.case_id,
                priority=DeadlinePriority.HIGH,
                ccp_section="CCP 2034.220"
            ))

        if cmo.expert_designation_defendant:
            deadlines.append(Deadline(
                title="Expert Designation (Defendant)",
                deadline_type=DeadlineType.EXPERT_DESIGNATION_DUE,
                due_date=cmo.expert_designation_defendant,
                case_id=cmo.case_id,
                priority=DeadlinePriority.HIGH,
                ccp_section="CCP 2034.220"
            ))

        # MSJ Deadlines
        if cmo.msj_filing_cutoff:
            deadlines.append(Deadline(
                title="MSJ Filing Cutoff",
                deadline_type=DeadlineType.MSJ_FILING,
                due_date=cmo.msj_filing_cutoff,
                case_id=cmo.case_id,
                priority=DeadlinePriority.HIGH,
                ccp_section="CCP 437c(a)"
            ))

        # Motions in Limine
        if cmo.motions_in_limine_cutoff:
            deadlines.append(Deadline(
                title="Motions in Limine Cutoff",
                deadline_type=DeadlineType.MOTION_FILING,
                due_date=cmo.motions_in_limine_cutoff,
                case_id=cmo.case_id,
                priority=DeadlinePriority.HIGH
            ))

        # Trial Preparation
        if cmo.jury_instructions_due:
            deadlines.append(Deadline(
                title="Jury Instructions Due",
                deadline_type=DeadlineType.CMO_DEADLINE,
                due_date=cmo.jury_instructions_due,
                case_id=cmo.case_id,
                priority=DeadlinePriority.MEDIUM
            ))

        if cmo.exhibit_list_due:
            deadlines.append(Deadline(
                title="Exhibit List Due",
                deadline_type=DeadlineType.CMO_DEADLINE,
                due_date=cmo.exhibit_list_due,
                case_id=cmo.case_id,
                priority=DeadlinePriority.MEDIUM
            ))

        if cmo.witness_list_due:
            deadlines.append(Deadline(
                title="Witness List Due",
                deadline_type=DeadlineType.CMO_DEADLINE,
                due_date=cmo.witness_list_due,
                case_id=cmo.case_id,
                priority=DeadlinePriority.MEDIUM
            ))

        if cmo.trial_brief_due:
            deadlines.append(Deadline(
                title="Trial Brief Due",
                deadline_type=DeadlineType.CMO_DEADLINE,
                due_date=cmo.trial_brief_due,
                case_id=cmo.case_id,
                priority=DeadlinePriority.MEDIUM
            ))

        # ADR Deadlines
        if cmo.mediation_deadline:
            deadlines.append(Deadline(
                title="Mediation Deadline",
                deadline_type=DeadlineType.CMO_DEADLINE,
                due_date=cmo.mediation_deadline,
                case_id=cmo.case_id,
                priority=DeadlinePriority.MEDIUM
            ))

        # Custom deadlines
        for custom in cmo.custom_deadlines:
            if not custom.is_completed:
                deadlines.append(Deadline(
                    title=custom.name,
                    deadline_type=custom.deadline_type,
                    due_date=custom.due_date,
                    case_id=cmo.case_id,
                    priority=DeadlinePriority.MEDIUM,
                    notes=custom.description
                ))

        return deadlines

    def get_upcoming_cmo_deadlines(self, case_id: str, days_ahead: int = 30) -> List[tuple]:
        """Get upcoming CMO deadlines for a case."""
        cmo = self.get_current_cmo(case_id)
        if not cmo:
            return []
        return cmo.get_upcoming_deadlines(days_ahead)

    def generate_cmo_report(self, case_id: str) -> str:
        """Generate a CMO summary report."""
        cmo = self.get_current_cmo(case_id)
        if not cmo:
            return f"No active Case Management Order for case {case_id}"

        lines = [
            "CASE MANAGEMENT ORDER SUMMARY",
            "=" * 60,
            f"Case ID: {case_id}",
            f"Order Date: {cmo.order_date.strftime('%m/%d/%Y')}",
        ]

        if cmo.judge_name:
            lines.append(f"Judge: {cmo.judge_name}")
        if cmo.department:
            lines.append(f"Department: {cmo.department}")

        lines.append("")
        lines.append("KEY DATES:")
        lines.append("-" * 40)

        all_deadlines = cmo.get_all_deadlines()
        for name, deadline_date in all_deadlines:
            days = (deadline_date - date.today()).days
            status = ""
            if days < 0:
                status = " [PAST DUE]"
            elif days <= 7:
                status = " [URGENT]"
            elif days <= 30:
                status = " [UPCOMING]"

            lines.append(f"  {deadline_date.strftime('%m/%d/%Y')}  {name}{status}")

        lines.append("")
        lines.append("=" * 60)

        return '\n'.join(lines)

    def export_cmos(self, case_id: str) -> List[dict]:
        """Export all CMOs for a case."""
        cmos = self.get_case_cmos(case_id, include_superseded=True)
        return [c.to_dict() for c in cmos]

    def import_cmo(self, cmo_data: dict) -> CaseManagementOrder:
        """Import a CMO from dict."""
        cmo = CaseManagementOrder.from_dict(cmo_data)
        return self.add_cmo(cmo)
