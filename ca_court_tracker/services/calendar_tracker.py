"""
Court Calendar Tracker

Tracks court calendar events for California civil cases including
hearings, conferences, and trial dates.
"""

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import Optional, List, Dict, Tuple
from uuid import uuid4

from ..models.event import CourtEvent, EventType, EventStatus, EventResult
from ..models.deadline import Deadline, DeadlineType, DeadlinePriority
from .deadline_calculator import DeadlineCalculator


class CalendarTracker:
    """
    Manages court calendar events for California civil cases.

    Provides functionality to:
    - Track court hearings, conferences, and trial dates
    - Calculate motion filing deadlines based on hearing dates
    - Track hearing results and follow-up events
    - Generate calendar reports
    """

    def __init__(self):
        """Initialize the calendar tracker."""
        self.events: Dict[str, CourtEvent] = {}  # event_id -> CourtEvent
        self.case_events: Dict[str, List[str]] = {}  # case_id -> [event_ids]
        self.deadline_calculator = DeadlineCalculator()

    def add_event(self, event: CourtEvent) -> CourtEvent:
        """Add an event to the calendar."""
        self.events[event.id] = event

        if event.case_id not in self.case_events:
            self.case_events[event.case_id] = []
        self.case_events[event.case_id].append(event.id)

        return event

    def create_event(self, title: str, event_type: EventType, event_date: date,
                     case_id: str, **kwargs) -> CourtEvent:
        """Create and add a new calendar event."""
        event = CourtEvent(
            title=title,
            event_type=event_type,
            event_date=event_date,
            case_id=case_id,
            **kwargs
        )
        return self.add_event(event)

    def get_event(self, event_id: str) -> Optional[CourtEvent]:
        """Get an event by ID."""
        return self.events.get(event_id)

    def get_case_events(self, case_id: str, include_past: bool = True,
                        include_completed: bool = True) -> List[CourtEvent]:
        """Get all events for a case."""
        event_ids = self.case_events.get(case_id, [])
        events = [self.events[eid] for eid in event_ids if eid in self.events]

        if not include_past:
            events = [e for e in events if e.event_date >= date.today()]

        if not include_completed:
            events = [e for e in events if e.status != EventStatus.COMPLETED]

        return sorted(events, key=lambda e: e.event_date)

    def get_upcoming_events(self, case_id: str, days_ahead: int = 30) -> List[CourtEvent]:
        """Get upcoming events for a case."""
        today = date.today()
        cutoff = today + timedelta(days=days_ahead)

        events = self.get_case_events(case_id, include_past=False)
        return [e for e in events
                if today <= e.event_date <= cutoff
                and e.status not in [EventStatus.VACATED, EventStatus.CANCELLED]]

    def get_events_by_type(self, case_id: str, event_type: EventType) -> List[CourtEvent]:
        """Get events of a specific type."""
        events = self.get_case_events(case_id)
        return [e for e in events if e.event_type == event_type]

    def get_events_by_date(self, case_id: str, event_date: date) -> List[CourtEvent]:
        """Get events on a specific date."""
        events = self.get_case_events(case_id)
        return [e for e in events if e.event_date == event_date]

    def get_events_by_date_range(self, case_id: str, start_date: date,
                                  end_date: date) -> List[CourtEvent]:
        """Get events within a date range."""
        events = self.get_case_events(case_id)
        return [e for e in events if start_date <= e.event_date <= end_date]

    def get_next_hearing(self, case_id: str) -> Optional[CourtEvent]:
        """Get the next scheduled hearing for a case."""
        events = self.get_upcoming_events(case_id)
        hearings = [e for e in events if e.is_hearing()]
        return hearings[0] if hearings else None

    def get_next_conference(self, case_id: str) -> Optional[CourtEvent]:
        """Get the next scheduled conference for a case."""
        events = self.get_upcoming_events(case_id)
        conferences = [e for e in events if e.is_conference()]
        return conferences[0] if conferences else None

    def get_trial_date(self, case_id: str) -> Optional[CourtEvent]:
        """Get the trial date event for a case."""
        events = self.get_case_events(case_id)
        trials = [e for e in events
                  if e.is_trial() and e.status not in [EventStatus.VACATED, EventStatus.CANCELLED]]
        return trials[-1] if trials else None  # Return most recent trial setting

    def schedule_hearing(self, case_id: str, title: str, hearing_date: date,
                         hearing_time: Optional[time] = None,
                         department: Optional[str] = None,
                         event_type: EventType = EventType.MOTION_HEARING,
                         **kwargs) -> Tuple[CourtEvent, List[Deadline]]:
        """
        Schedule a hearing and create associated deadlines.

        Returns the event and list of deadlines (opposition, reply).
        """
        event = self.create_event(
            title=title,
            event_type=event_type,
            event_date=hearing_date,
            case_id=case_id,
            event_time=hearing_time,
            department=department,
            **kwargs
        )

        # Create deadlines based on hearing type
        deadlines = self.deadline_calculator.create_deadlines_for_hearing(event)

        # Link deadlines to event
        for deadline in deadlines:
            event.add_deadline(deadline.id)

        return event, deadlines

    def calculate_motion_filing_deadline(self, hearing_date: date,
                                          is_msj: bool = False) -> date:
        """Calculate when motion papers must be filed for a hearing."""
        if is_msj:
            deadlines = self.deadline_calculator.calculate_msj_deadlines(hearing_date)
        else:
            deadlines = self.deadline_calculator.calculate_motion_deadlines(hearing_date)

        return deadlines['moving_papers_deadline']

    def continue_event(self, event_id: str, new_date: date,
                       reason: Optional[str] = None) -> Optional[CourtEvent]:
        """Continue an event to a new date."""
        event = self.events.get(event_id)
        if not event:
            return None

        # Create new event for the continued date
        new_event = CourtEvent(
            title=event.title,
            event_type=event.event_type,
            event_date=new_date,
            case_id=event.case_id,
            event_time=event.event_time,
            department=event.department,
            judge_name=event.judge_name,
            related_document_ids=event.related_document_ids.copy(),
            parties_required=event.parties_required.copy(),
            is_mandatory=event.is_mandatory,
            requires_appearance=event.requires_appearance,
            notes=f"Continued from {event.event_date.isoformat()}"
        )

        # Mark original event as continued
        event.continue_to(new_date, reason)
        event.next_event_id = new_event.id

        self.add_event(new_event)
        return new_event

    def vacate_event(self, event_id: str, reason: Optional[str] = None) -> bool:
        """Vacate a scheduled event."""
        event = self.events.get(event_id)
        if event:
            event.vacate(reason)
            return True
        return False

    def complete_event(self, event_id: str, result: EventResult,
                       ruling_summary: Optional[str] = None,
                       minute_order_id: Optional[str] = None) -> bool:
        """Mark an event as completed with a result."""
        event = self.events.get(event_id)
        if event:
            event.complete(result, ruling_summary)
            if minute_order_id:
                event.minute_order_id = minute_order_id
            return True
        return False

    def link_document_to_event(self, event_id: str, document_id: str) -> bool:
        """Link a document to an event."""
        event = self.events.get(event_id)
        if event:
            event.add_related_document(document_id)
            return True
        return False

    def get_events_by_result(self, case_id: str, result: EventResult) -> List[CourtEvent]:
        """Get events with a specific result."""
        events = self.get_case_events(case_id)
        return [e for e in events if e.result == result]

    def get_pending_hearings(self, case_id: str) -> List[CourtEvent]:
        """Get hearings that have not yet occurred."""
        today = date.today()
        events = self.get_case_events(case_id)
        return [e for e in events
                if e.is_hearing()
                and e.event_date >= today
                and e.status in [EventStatus.SCHEDULED, EventStatus.CONFIRMED, EventStatus.TENTATIVE]]

    def get_events_requiring_appearance(self, case_id: str, party_id: Optional[str] = None) -> List[CourtEvent]:
        """Get events that require an appearance."""
        events = self.get_upcoming_events(case_id)
        result = [e for e in events if e.requires_appearance]

        if party_id:
            result = [e for e in result if party_id in e.parties_required or not e.parties_required]

        return result

    def get_today_events(self, case_id: str) -> List[CourtEvent]:
        """Get events scheduled for today."""
        return self.get_events_by_date(case_id, date.today())

    def get_week_events(self, case_id: str) -> List[CourtEvent]:
        """Get events scheduled for this week."""
        today = date.today()
        week_end = today + timedelta(days=7)
        return self.get_events_by_date_range(case_id, today, week_end)

    def get_calendar_statistics(self, case_id: str) -> dict:
        """Get calendar statistics for a case."""
        events = self.get_case_events(case_id)

        stats = {
            'total_events': len(events),
            'upcoming': 0,
            'completed': 0,
            'continued': 0,
            'vacated': 0,
            'hearings': 0,
            'conferences': 0,
            'trials': 0,
            'by_type': {},
            'by_result': {},
        }

        today = date.today()

        for event in events:
            # Count by status
            if event.event_date >= today and event.status not in [EventStatus.VACATED, EventStatus.CANCELLED]:
                stats['upcoming'] += 1
            if event.status == EventStatus.COMPLETED:
                stats['completed'] += 1
            if event.status == EventStatus.CONTINUED:
                stats['continued'] += 1
            if event.status in [EventStatus.VACATED, EventStatus.CANCELLED]:
                stats['vacated'] += 1

            # Count by category
            if event.is_hearing():
                stats['hearings'] += 1
            if event.is_conference():
                stats['conferences'] += 1
            if event.is_trial():
                stats['trials'] += 1

            # Count by type
            type_name = event.event_type.value
            stats['by_type'][type_name] = stats['by_type'].get(type_name, 0) + 1

            # Count by result
            if event.result:
                result_name = event.result.value
                stats['by_result'][result_name] = stats['by_result'].get(result_name, 0) + 1

        return stats

    def generate_calendar_report(self, case_id: str, days_ahead: int = 60) -> str:
        """Generate a calendar report for a case."""
        lines = [
            "COURT CALENDAR REPORT",
            "=" * 70,
            f"Case ID: {case_id}",
            f"Generated: {datetime.now().strftime('%m/%d/%Y %H:%M')}",
            "",
        ]

        # Upcoming events
        upcoming = self.get_upcoming_events(case_id, days_ahead)
        if upcoming:
            lines.append("UPCOMING EVENTS:")
            lines.append("-" * 70)

            for event in upcoming:
                date_str = event.event_date.strftime('%m/%d/%Y')
                time_str = event.get_display_time()
                location = event.get_display_location()
                days = event.days_until()

                status_indicator = ""
                if days <= 3:
                    status_indicator = " [URGENT]"
                elif days <= 7:
                    status_indicator = " [SOON]"

                lines.append(f"  {date_str} {time_str}  {event.title}{status_indicator}")
                lines.append(f"      Type: {event.event_type.value}")
                lines.append(f"      Location: {location}")
                lines.append(f"      Days Until: {days}")
                lines.append("")
        else:
            lines.append("No upcoming events in the next {days_ahead} days.")

        # Recent past events
        past_events = [e for e in self.get_case_events(case_id)
                       if e.event_date < date.today() and e.status == EventStatus.COMPLETED][-5:]

        if past_events:
            lines.append("")
            lines.append("RECENT COMPLETED EVENTS:")
            lines.append("-" * 70)

            for event in reversed(past_events):
                date_str = event.event_date.strftime('%m/%d/%Y')
                result_str = event.result.value if event.result else "N/A"
                lines.append(f"  {date_str}  {event.title}")
                lines.append(f"      Result: {result_str}")
                if event.ruling_summary:
                    lines.append(f"      Ruling: {event.ruling_summary[:60]}...")
                lines.append("")

        lines.append("=" * 70)

        return '\n'.join(lines)

    def export_events(self, case_id: str) -> List[dict]:
        """Export all events for a case."""
        events = self.get_case_events(case_id)
        return [e.to_dict() for e in events]

    def import_event(self, event_data: dict) -> CourtEvent:
        """Import an event from dict."""
        event = CourtEvent.from_dict(event_data)
        return self.add_event(event)

    def get_events_for_reminder(self, case_id: str, reminder_days: List[int] = None) -> List[Tuple[CourtEvent, int]]:
        """
        Get events that need reminders sent.

        Returns list of (event, days_until) tuples.
        """
        if reminder_days is None:
            reminder_days = [7, 3, 1]

        today = date.today()
        result = []

        events = self.get_upcoming_events(case_id)
        for event in events:
            days = event.days_until()
            if days in reminder_days and today not in event.reminders_sent:
                result.append((event, days))

        return result

    def mark_reminder_sent(self, event_id: str) -> bool:
        """Mark that a reminder was sent for an event."""
        event = self.events.get(event_id)
        if event:
            event.reminders_sent.append(date.today())
            return True
        return False
