"""
California Deadline Calculator

Calculates legal deadlines based on:
- California Code of Civil Procedure (CCP)
- California Rules of Court (CRC)
- Local court rules

Handles service method extensions, court day calculations,
and holiday adjustments per California law.
"""

from datetime import date, datetime, timedelta
from typing import Optional, List, Tuple
from enum import Enum

from ..models.document import Document, DocumentType, ServiceMethod
from ..models.event import CourtEvent, EventType
from ..models.deadline import Deadline, DeadlineType, DeadlinePriority


class DeadlineCalculator:
    """
    Calculates legal deadlines for California civil litigation.

    Implements deadline calculations per California Code of Civil Procedure
    and California Rules of Court.
    """

    # California state holidays (observed dates may vary by year)
    # These are the standard holidays when courts are closed
    CALIFORNIA_HOLIDAYS = {
        "New Year's Day",
        "Martin Luther King Jr. Day",
        "Presidents' Day",
        "Cesar Chavez Day",
        "Memorial Day",
        "Independence Day",
        "Labor Day",
        "Indigenous Peoples' Day",
        "Veterans Day",
        "Thanksgiving Day",
        "Day after Thanksgiving",
        "Christmas Day",
    }

    # Service method extensions per CCP 1013 and 1010.6
    SERVICE_EXTENSIONS = {
        ServiceMethod.PERSONAL_SERVICE: 0,
        ServiceMethod.ELECTRONIC_SERVICE: 2,  # CCP 1010.6(a)(3)(B)
        ServiceMethod.ONELEGAL: 2,  # Electronic service
        ServiceMethod.MAIL_SERVICE: 5,  # CCP 1013(a) - within CA
        ServiceMethod.FAX_SERVICE: 2,  # CCP 1013(e)
        ServiceMethod.OVERNIGHT_DELIVERY: 2,  # CCP 1013(c)
    }

    # Extended mail service for out-of-state/country
    MAIL_EXTENSION_OUT_OF_STATE = 10  # CCP 1013(a)
    MAIL_EXTENSION_OUT_OF_COUNTRY = 20  # CCP 1013(a)

    # Discovery response deadlines (calendar days from service)
    DISCOVERY_DEADLINES = {
        DocumentType.INTERROGATORIES: 30,  # CCP 2030.260
        DocumentType.REQUESTS_FOR_PRODUCTION: 30,  # CCP 2031.260
        DocumentType.REQUESTS_FOR_ADMISSION: 30,  # CCP 2033.250
        DocumentType.DEPOSITION_NOTICE: 20,  # Objection deadline
    }

    # Motion hearing deadlines (court days before hearing unless noted)
    MOTION_DEADLINES = {
        'notice': 16,  # CCP 1005(b) - calendar days
        'opposition': 9,  # CCP 1005(b) - court days
        'reply': 5,  # CCP 1005(b) - court days
    }

    # Summary Judgment/Adjudication specific deadlines
    MSJ_DEADLINES = {
        'notice': 75,  # CCP 437c(a) - calendar days before hearing
        'opposition': 14,  # CCP 437c(b)(2) - calendar days before hearing
        'reply': 5,  # CCP 437c(b)(3) - calendar days before hearing
        'moving_papers': 75,  # Same as notice
    }

    # Ex Parte deadlines
    EX_PARTE_NOTICE_HOURS = 24  # CRC 3.1203

    def __init__(self):
        """Initialize the deadline calculator."""
        self._holidays_cache: dict = {}

    def get_california_holidays(self, year: int) -> List[date]:
        """
        Get California court holidays for a given year.

        Returns list of dates when California courts are closed.
        """
        if year in self._holidays_cache:
            return self._holidays_cache[year]

        holidays = []

        # New Year's Day - January 1
        holidays.append(self._adjust_holiday(date(year, 1, 1)))

        # Martin Luther King Jr. Day - Third Monday in January
        holidays.append(self._nth_weekday(year, 1, 0, 3))  # 3rd Monday

        # Presidents' Day - Third Monday in February
        holidays.append(self._nth_weekday(year, 2, 0, 3))

        # Cesar Chavez Day - March 31
        holidays.append(self._adjust_holiday(date(year, 3, 31)))

        # Memorial Day - Last Monday in May
        holidays.append(self._last_weekday(year, 5, 0))

        # Independence Day - July 4
        holidays.append(self._adjust_holiday(date(year, 7, 4)))

        # Labor Day - First Monday in September
        holidays.append(self._nth_weekday(year, 9, 0, 1))

        # Indigenous Peoples' Day - Second Monday in October
        holidays.append(self._nth_weekday(year, 10, 0, 2))

        # Veterans Day - November 11
        holidays.append(self._adjust_holiday(date(year, 11, 11)))

        # Thanksgiving Day - Fourth Thursday in November
        holidays.append(self._nth_weekday(year, 11, 3, 4))

        # Day after Thanksgiving
        thanksgiving = self._nth_weekday(year, 11, 3, 4)
        holidays.append(thanksgiving + timedelta(days=1))

        # Christmas Day - December 25
        holidays.append(self._adjust_holiday(date(year, 12, 25)))

        self._holidays_cache[year] = holidays
        return holidays

    def _adjust_holiday(self, holiday: date) -> date:
        """Adjust holiday if it falls on weekend."""
        if holiday.weekday() == 5:  # Saturday
            return holiday - timedelta(days=1)  # Observed Friday
        elif holiday.weekday() == 6:  # Sunday
            return holiday + timedelta(days=1)  # Observed Monday
        return holiday

    def _nth_weekday(self, year: int, month: int, weekday: int, n: int) -> date:
        """Get the nth occurrence of a weekday in a month."""
        first_day = date(year, month, 1)
        first_weekday = first_day + timedelta(days=(weekday - first_day.weekday()) % 7)
        return first_weekday + timedelta(weeks=n - 1)

    def _last_weekday(self, year: int, month: int, weekday: int) -> date:
        """Get the last occurrence of a weekday in a month."""
        if month == 12:
            next_month = date(year + 1, 1, 1)
        else:
            next_month = date(year, month + 1, 1)
        last_day = next_month - timedelta(days=1)
        days_back = (last_day.weekday() - weekday) % 7
        return last_day - timedelta(days=days_back)

    def is_court_day(self, check_date: date) -> bool:
        """
        Check if a date is a court day (not weekend or holiday).

        Per CCP 12a, court days exclude Saturdays, Sundays,
        and judicial holidays.
        """
        # Check weekend
        if check_date.weekday() >= 5:
            return False

        # Check holidays
        holidays = self.get_california_holidays(check_date.year)
        if check_date in holidays:
            return False

        return True

    def add_calendar_days(self, start_date: date, days: int,
                          exclude_end_if_weekend_holiday: bool = True) -> date:
        """
        Add calendar days to a date.

        Per CCP 12a, if the last day falls on a weekend or holiday,
        it extends to the next court day.
        """
        result_date = start_date + timedelta(days=days)

        if exclude_end_if_weekend_holiday:
            while not self.is_court_day(result_date):
                result_date += timedelta(days=1)

        return result_date

    def add_court_days(self, start_date: date, court_days: int) -> date:
        """
        Add court days to a date.

        Court days exclude weekends and judicial holidays per CCP 12a.
        """
        result_date = start_date
        days_added = 0

        while days_added < court_days:
            result_date += timedelta(days=1)
            if self.is_court_day(result_date):
                days_added += 1

        return result_date

    def subtract_court_days(self, end_date: date, court_days: int) -> date:
        """
        Subtract court days from a date (counting backwards).

        Used for calculating "X court days before hearing" deadlines.
        """
        result_date = end_date
        days_subtracted = 0

        while days_subtracted < court_days:
            result_date -= timedelta(days=1)
            if self.is_court_day(result_date):
                days_subtracted += 1

        return result_date

    def subtract_calendar_days(self, end_date: date, days: int) -> date:
        """Subtract calendar days from a date."""
        return end_date - timedelta(days=days)

    def get_service_extension(self, service_method: ServiceMethod,
                               out_of_state: bool = False,
                               out_of_country: bool = False) -> int:
        """
        Get the service extension days for a given service method.

        Based on CCP 1013 and 1010.6.
        """
        if service_method == ServiceMethod.MAIL_SERVICE:
            if out_of_country:
                return self.MAIL_EXTENSION_OUT_OF_COUNTRY
            elif out_of_state:
                return self.MAIL_EXTENSION_OUT_OF_STATE
            return self.SERVICE_EXTENSIONS[ServiceMethod.MAIL_SERVICE]

        return self.SERVICE_EXTENSIONS.get(service_method, 0)

    def calculate_response_deadline(self, document: Document,
                                     service_method: ServiceMethod,
                                     service_date: date,
                                     out_of_state: bool = False,
                                     out_of_country: bool = False) -> Optional[date]:
        """
        Calculate response deadline for a document.

        Takes into account document type base deadline and service extensions.
        """
        base_days = document.get_response_deadline_days()
        if base_days is None:
            return None

        service_extension = self.get_service_extension(
            service_method, out_of_state, out_of_country
        )

        total_days = base_days + service_extension
        return self.add_calendar_days(service_date, total_days)

    def calculate_discovery_response_deadline(self,
                                               discovery_type: DocumentType,
                                               service_date: date,
                                               service_method: ServiceMethod,
                                               out_of_state: bool = False) -> Tuple[date, str]:
        """
        Calculate discovery response deadline.

        Returns (deadline_date, ccp_section).
        """
        base_days = self.DISCOVERY_DEADLINES.get(discovery_type)
        if base_days is None:
            raise ValueError(f"Unknown discovery type: {discovery_type}")

        service_extension = self.get_service_extension(
            service_method, out_of_state
        )

        deadline = self.add_calendar_days(service_date, base_days + service_extension)

        ccp_sections = {
            DocumentType.INTERROGATORIES: "CCP 2030.260",
            DocumentType.REQUESTS_FOR_PRODUCTION: "CCP 2031.260",
            DocumentType.REQUESTS_FOR_ADMISSION: "CCP 2033.250",
            DocumentType.DEPOSITION_NOTICE: "CCP 2025.410",
        }

        return deadline, ccp_sections.get(discovery_type, "")

    def calculate_motion_deadlines(self, hearing_date: date,
                                    service_method: ServiceMethod = ServiceMethod.ELECTRONIC_SERVICE
                                    ) -> dict:
        """
        Calculate motion deadlines for a hearing.

        Returns dict with notice, opposition, and reply deadlines.
        Based on CCP 1005(b).
        """
        service_ext = self.get_service_extension(service_method)

        # Notice: 16 calendar days + 2 court days before hearing, plus service extension
        notice_base = self.subtract_calendar_days(hearing_date, 16)
        notice_with_service = self.subtract_court_days(notice_base, 2)
        notice_deadline = self.subtract_calendar_days(notice_with_service, service_ext)

        # Opposition: 9 court days before hearing
        opposition_deadline = self.subtract_court_days(hearing_date, 9)

        # Reply: 5 court days before hearing
        reply_deadline = self.subtract_court_days(hearing_date, 5)

        return {
            'hearing_date': hearing_date,
            'notice_deadline': notice_deadline,
            'moving_papers_deadline': notice_deadline,  # Same as notice
            'opposition_deadline': opposition_deadline,
            'reply_deadline': reply_deadline,
            'ccp_section': 'CCP 1005(b)',
        }

    def calculate_msj_deadlines(self, hearing_date: date,
                                 trial_date: Optional[date] = None) -> dict:
        """
        Calculate Summary Judgment/Adjudication motion deadlines.

        Based on CCP 437c.
        """
        # MSJ must be heard at least 30 days before trial
        if trial_date:
            latest_hearing = self.subtract_calendar_days(trial_date, 30)
            if hearing_date > latest_hearing:
                hearing_date = latest_hearing

        # Notice/Moving papers: 75 calendar days before hearing
        notice_deadline = self.subtract_calendar_days(hearing_date, 75)

        # Opposition: 14 calendar days before hearing
        opposition_deadline = self.subtract_calendar_days(hearing_date, 14)

        # Reply: 5 calendar days before hearing
        reply_deadline = self.subtract_calendar_days(hearing_date, 5)

        return {
            'hearing_date': hearing_date,
            'notice_deadline': notice_deadline,
            'moving_papers_deadline': notice_deadline,
            'opposition_deadline': opposition_deadline,
            'reply_deadline': reply_deadline,
            'ccp_section': 'CCP 437c',
            'minimum_days_before_trial': 30,
        }

    def calculate_demurrer_deadlines(self, hearing_date: date) -> dict:
        """
        Calculate demurrer motion deadlines.

        Based on CCP 430.40 and CCP 1005.
        """
        # Demurrer must be filed within 30 days of service of complaint
        # but for hearing deadlines, use standard motion rules

        return self.calculate_motion_deadlines(hearing_date)

    def calculate_answer_deadline(self, service_date: date,
                                   service_method: ServiceMethod,
                                   is_unlawful_detainer: bool = False) -> Tuple[date, str]:
        """
        Calculate deadline to file Answer to Complaint.

        Based on CCP 412.20 (30 days) or CCP 1167 (5 days for UD).
        """
        if is_unlawful_detainer:
            # Unlawful detainer: 5 calendar days
            base_days = 5
            ccp_section = "CCP 1167"
        else:
            # Standard: 30 calendar days
            base_days = 30
            ccp_section = "CCP 412.20"

        service_ext = self.get_service_extension(service_method)
        deadline = self.add_calendar_days(service_date, base_days + service_ext)

        return deadline, ccp_section

    def calculate_trial_related_deadlines(self, trial_date: date,
                                           case_type: str = "unlimited") -> dict:
        """
        Calculate key deadlines leading up to trial.

        Returns dict of deadline names to dates.
        """
        deadlines = {}

        # Final Status Conference - typically 10-14 days before trial
        deadlines['fsc'] = self.subtract_calendar_days(trial_date, 14)

        # MSJ hearing cutoff - 30 days before trial (CCP 437c(a))
        deadlines['msj_hearing_cutoff'] = self.subtract_calendar_days(trial_date, 30)

        # MSJ filing deadline - 75 days before MSJ hearing cutoff
        msj_hearing_cutoff = deadlines['msj_hearing_cutoff']
        deadlines['msj_filing_cutoff'] = self.subtract_calendar_days(msj_hearing_cutoff, 75)

        # Expert discovery cutoff - typically 15 days before trial
        deadlines['expert_discovery_cutoff'] = self.subtract_calendar_days(trial_date, 15)

        # Fact discovery cutoff - typically 30 days before trial
        deadlines['fact_discovery_cutoff'] = self.subtract_calendar_days(trial_date, 30)

        # Expert designation - initial (50 days before expert cutoff)
        deadlines['expert_designation_initial'] = self.subtract_calendar_days(
            deadlines['expert_discovery_cutoff'], 50
        )

        # Motions in limine - typically 15 days before trial
        deadlines['motions_in_limine'] = self.subtract_calendar_days(trial_date, 15)

        # Jury instructions - varies by local rule, typically 10 days before trial
        deadlines['jury_instructions'] = self.subtract_calendar_days(trial_date, 10)

        # Witness list - varies by local rule
        deadlines['witness_list'] = self.subtract_calendar_days(trial_date, 15)

        # Exhibit list - varies by local rule
        deadlines['exhibit_list'] = self.subtract_calendar_days(trial_date, 15)

        # Trial brief - varies by local rule
        deadlines['trial_brief'] = self.subtract_calendar_days(trial_date, 10)

        return deadlines

    def calculate_cmc_deadlines(self, cmc_date: date) -> dict:
        """
        Calculate Case Management Conference related deadlines.

        Returns dict of deadline names to dates.
        """
        # CMC Statement due 15 days before CMC (CRC 3.725)
        cmc_statement = self.subtract_calendar_days(cmc_date, 15)

        # Meet and confer before filing CMC statement
        meet_and_confer = self.subtract_calendar_days(cmc_statement, 5)

        return {
            'cmc_date': cmc_date,
            'cmc_statement_deadline': cmc_statement,
            'meet_and_confer_deadline': meet_and_confer,
            'crc_rule': 'CRC 3.725',
        }

    def create_deadline_from_document(self, document: Document,
                                       service_date: date,
                                       service_method: ServiceMethod,
                                       responsible_party_id: Optional[str] = None,
                                       responsible_party_name: Optional[str] = None) -> Optional[Deadline]:
        """
        Create a Deadline object from a document requiring response.
        """
        if not document.requires_response:
            # Check if document type typically requires response
            if document.document_type not in self.DISCOVERY_DEADLINES and \
               document.document_type not in [DocumentType.COMPLAINT, DocumentType.CROSS_COMPLAINT,
                                              DocumentType.AMENDED_COMPLAINT, DocumentType.DEMURRER]:
                return None

        # Calculate deadline
        due_date = self.calculate_response_deadline(document, service_method, service_date)
        if due_date is None:
            return None

        # Determine deadline type
        deadline_type_map = {
            DocumentType.COMPLAINT: DeadlineType.ANSWER_DUE,
            DocumentType.CROSS_COMPLAINT: DeadlineType.ANSWER_DUE,
            DocumentType.AMENDED_COMPLAINT: DeadlineType.ANSWER_DUE,
            DocumentType.INTERROGATORIES: DeadlineType.DISCOVERY_RESPONSE_DUE,
            DocumentType.REQUESTS_FOR_PRODUCTION: DeadlineType.DISCOVERY_RESPONSE_DUE,
            DocumentType.REQUESTS_FOR_ADMISSION: DeadlineType.DISCOVERY_RESPONSE_DUE,
            DocumentType.MOTION: DeadlineType.OPPOSITION_DUE,
            DocumentType.MOTION_TO_COMPEL: DeadlineType.OPPOSITION_DUE,
            DocumentType.DEMURRER: DeadlineType.OPPOSITION_DUE,
        }

        deadline_type = deadline_type_map.get(document.document_type, DeadlineType.CUSTOM)

        # Determine priority
        priority = DeadlinePriority.MEDIUM
        if document.document_type in [DocumentType.COMPLAINT, DocumentType.REQUESTS_FOR_ADMISSION]:
            priority = DeadlinePriority.HIGH  # RFAs deemed admitted if not responded
        elif document.document_type == DocumentType.MOTION_FOR_SUMMARY_JUDGMENT:
            priority = DeadlinePriority.CRITICAL

        # Get CCP section
        ccp_sections = {
            DocumentType.COMPLAINT: "CCP 412.20",
            DocumentType.INTERROGATORIES: "CCP 2030.260",
            DocumentType.REQUESTS_FOR_PRODUCTION: "CCP 2031.260",
            DocumentType.REQUESTS_FOR_ADMISSION: "CCP 2033.250",
        }

        deadline = Deadline(
            title=f"Response to {document.title}",
            deadline_type=deadline_type,
            due_date=due_date,
            case_id=document.case_id,
            priority=priority,
            trigger_date=service_date,
            trigger_document_id=document.id,
            base_days=document.get_response_deadline_days(),
            service_extension_days=self.get_service_extension(service_method),
            response_to_document_id=document.id,
            responsible_party_id=responsible_party_id,
            responsible_party_name=responsible_party_name,
            ccp_section=ccp_sections.get(document.document_type),
        )

        return deadline

    def create_deadlines_for_hearing(self, event: CourtEvent,
                                      moving_party_id: Optional[str] = None,
                                      responding_party_id: Optional[str] = None) -> List[Deadline]:
        """
        Create deadline objects for a hearing event.
        """
        deadlines = []

        if event.event_type == EventType.MSJ_HEARING:
            calc_deadlines = self.calculate_msj_deadlines(event.event_date)
        else:
            calc_deadlines = self.calculate_motion_deadlines(event.event_date)

        # Opposition deadline
        opposition = Deadline(
            title=f"Opposition to {event.title}",
            deadline_type=DeadlineType.OPPOSITION_DUE,
            due_date=calc_deadlines['opposition_deadline'],
            case_id=event.case_id,
            priority=DeadlinePriority.HIGH,
            related_event_id=event.id,
            responsible_party_id=responding_party_id,
            court_days=event.event_type != EventType.MSJ_HEARING,
            ccp_section=calc_deadlines.get('ccp_section'),
        )
        deadlines.append(opposition)

        # Reply deadline
        reply = Deadline(
            title=f"Reply re {event.title}",
            deadline_type=DeadlineType.REPLY_DUE,
            due_date=calc_deadlines['reply_deadline'],
            case_id=event.case_id,
            priority=DeadlinePriority.MEDIUM,
            related_event_id=event.id,
            responsible_party_id=moving_party_id,
            court_days=event.event_type != EventType.MSJ_HEARING,
            ccp_section=calc_deadlines.get('ccp_section'),
        )
        deadlines.append(reply)

        return deadlines
