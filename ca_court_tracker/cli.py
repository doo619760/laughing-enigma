#!/usr/bin/env python3
"""
California Court Case Tracker CLI

Command-line interface for managing California court cases,
tracking deadlines, and managing court filings.
"""

import argparse
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

from .models.case import Case, CaseType, CaseStatus
from .models.party import PartyType
from .models.document import DocumentType, ServiceMethod
from .models.event import EventType, EventResult
from .models.deadline import DeadlineStatus
from .services.case_manager import CaseManager
from .utils.date_utils import parse_date, format_date, format_relative_date


class CourtTrackerCLI:
    """Command-line interface for the California Court Case Tracker."""

    def __init__(self, data_dir: Optional[str] = None):
        """Initialize the CLI with optional data directory."""
        self.data_dir = data_dir or str(Path.home() / '.ca_court_tracker')
        self.manager = CaseManager(self.data_dir)

        # Try to load existing data
        self.manager.load()

    def run(self, args: Optional[list] = None):
        """Run the CLI with the given arguments."""
        parser = self._create_parser()
        parsed_args = parser.parse_args(args)

        if hasattr(parsed_args, 'func'):
            parsed_args.func(parsed_args)
        else:
            parser.print_help()

    def _create_parser(self) -> argparse.ArgumentParser:
        """Create the argument parser."""
        parser = argparse.ArgumentParser(
            description='California Court Case Tracker',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  %(prog)s case create --number 24STCV01234 --name "Smith v. Jones" --type unlimited_civil --court "Los Angeles Superior Court" --county "Los Angeles"
  %(prog)s case list
  %(prog)s deadline list --case 24STCV01234
  %(prog)s deadline upcoming
  %(prog)s calculate deadline --from 2024-01-15 --days 30 --service electronic
            """
        )

        subparsers = parser.add_subparsers(title='commands', dest='command')

        # Case commands
        self._add_case_commands(subparsers)

        # Party commands
        self._add_party_commands(subparsers)

        # Document commands
        self._add_document_commands(subparsers)

        # Deadline commands
        self._add_deadline_commands(subparsers)

        # Event commands
        self._add_event_commands(subparsers)

        # Calculate commands
        self._add_calculate_commands(subparsers)

        # Report commands
        self._add_report_commands(subparsers)

        return parser

    def _add_case_commands(self, subparsers):
        """Add case-related commands."""
        case_parser = subparsers.add_parser('case', help='Case management commands')
        case_sub = case_parser.add_subparsers(dest='case_command')

        # case create
        create = case_sub.add_parser('create', help='Create a new case')
        create.add_argument('--number', '-n', required=True, help='Case number')
        create.add_argument('--name', required=True, help='Case name')
        create.add_argument('--type', '-t', required=True,
                           choices=[t.value for t in CaseType],
                           help='Case type')
        create.add_argument('--court', '-c', required=True, help='Court name')
        create.add_argument('--county', required=True, help='County')
        create.add_argument('--department', '-d', help='Department')
        create.add_argument('--judge', '-j', help='Judge name')
        create.add_argument('--filed', help='Filing date (MM/DD/YYYY)')
        create.add_argument('--trial', help='Trial date (MM/DD/YYYY)')
        create.set_defaults(func=self._cmd_case_create)

        # case list
        list_cmd = case_sub.add_parser('list', help='List all cases')
        list_cmd.add_argument('--status', '-s', choices=[s.value for s in CaseStatus],
                             help='Filter by status')
        list_cmd.set_defaults(func=self._cmd_case_list)

        # case show
        show = case_sub.add_parser('show', help='Show case details')
        show.add_argument('case_number', help='Case number')
        show.set_defaults(func=self._cmd_case_show)

        # case update
        update = case_sub.add_parser('update', help='Update case')
        update.add_argument('case_number', help='Case number')
        update.add_argument('--status', '-s', choices=[s.value for s in CaseStatus])
        update.add_argument('--department', '-d')
        update.add_argument('--judge', '-j')
        update.add_argument('--trial', help='Trial date')
        update.set_defaults(func=self._cmd_case_update)

    def _add_party_commands(self, subparsers):
        """Add party-related commands."""
        party_parser = subparsers.add_parser('party', help='Party management commands')
        party_sub = party_parser.add_subparsers(dest='party_command')

        # party add
        add = party_sub.add_parser('add', help='Add a party to a case')
        add.add_argument('--case', '-c', required=True, help='Case number')
        add.add_argument('--name', '-n', required=True, help='Party name')
        add.add_argument('--type', '-t', required=True,
                        choices=[t.value for t in PartyType],
                        help='Party type')
        add.add_argument('--attorney', '-a', help='Attorney name')
        add.add_argument('--email', '-e', help='Email address')
        add.add_argument('--phone', '-p', help='Phone number')
        add.set_defaults(func=self._cmd_party_add)

        # party list
        list_cmd = party_sub.add_parser('list', help='List parties for a case')
        list_cmd.add_argument('--case', '-c', required=True, help='Case number')
        list_cmd.set_defaults(func=self._cmd_party_list)

    def _add_document_commands(self, subparsers):
        """Add document-related commands."""
        doc_parser = subparsers.add_parser('document', help='Document management commands')
        doc_sub = doc_parser.add_subparsers(dest='doc_command')

        # document file
        file_cmd = doc_sub.add_parser('file', help='Record a filed document')
        file_cmd.add_argument('--case', '-c', required=True, help='Case number')
        file_cmd.add_argument('--title', '-t', required=True, help='Document title')
        file_cmd.add_argument('--type', required=True,
                             choices=[t.value for t in DocumentType],
                             help='Document type')
        file_cmd.add_argument('--date', '-d', required=True, help='Filing date')
        file_cmd.add_argument('--party', '-p', help='Filing party name')
        file_cmd.add_argument('--hearing', help='Associated hearing date')
        file_cmd.set_defaults(func=self._cmd_document_file)

        # document list
        list_cmd = doc_sub.add_parser('list', help='List documents for a case')
        list_cmd.add_argument('--case', '-c', required=True, help='Case number')
        list_cmd.add_argument('--type', '-t', help='Filter by document type')
        list_cmd.add_argument('--limit', '-l', type=int, default=20, help='Limit results')
        list_cmd.set_defaults(func=self._cmd_document_list)

        # document serve
        serve = doc_sub.add_parser('serve', help='Record service of a document')
        serve.add_argument('--document', '-d', required=True, help='Document ID')
        serve.add_argument('--party', '-p', required=True, help='Served party name')
        serve.add_argument('--method', '-m', required=True,
                          choices=[m.value for m in ServiceMethod],
                          help='Service method')
        serve.add_argument('--date', required=True, help='Service date')
        serve.set_defaults(func=self._cmd_document_serve)

    def _add_deadline_commands(self, subparsers):
        """Add deadline-related commands."""
        dl_parser = subparsers.add_parser('deadline', help='Deadline management commands')
        dl_sub = dl_parser.add_subparsers(dest='dl_command')

        # deadline list
        list_cmd = dl_sub.add_parser('list', help='List deadlines for a case')
        list_cmd.add_argument('--case', '-c', required=True, help='Case number')
        list_cmd.add_argument('--status', '-s', choices=[s.value for s in DeadlineStatus],
                             help='Filter by status')
        list_cmd.add_argument('--include-completed', action='store_true',
                             help='Include completed deadlines')
        list_cmd.set_defaults(func=self._cmd_deadline_list)

        # deadline upcoming
        upcoming = dl_sub.add_parser('upcoming', help='Show upcoming deadlines across all cases')
        upcoming.add_argument('--days', '-d', type=int, default=14,
                             help='Days ahead to look')
        upcoming.set_defaults(func=self._cmd_deadline_upcoming)

        # deadline complete
        complete = dl_sub.add_parser('complete', help='Mark a deadline as completed')
        complete.add_argument('deadline_id', help='Deadline ID')
        complete.set_defaults(func=self._cmd_deadline_complete)

        # deadline extend
        extend = dl_sub.add_parser('extend', help='Extend a deadline')
        extend.add_argument('deadline_id', help='Deadline ID')
        extend.add_argument('--date', '-d', required=True, help='New due date')
        extend.add_argument('--reason', '-r', required=True, help='Reason for extension')
        extend.add_argument('--stipulated', action='store_true', help='Stipulated extension')
        extend.add_argument('--court-ordered', action='store_true', help='Court ordered extension')
        extend.set_defaults(func=self._cmd_deadline_extend)

    def _add_event_commands(self, subparsers):
        """Add event-related commands."""
        event_parser = subparsers.add_parser('event', help='Calendar event commands')
        event_sub = event_parser.add_subparsers(dest='event_command')

        # event add
        add = event_sub.add_parser('add', help='Add a calendar event')
        add.add_argument('--case', '-c', required=True, help='Case number')
        add.add_argument('--title', '-t', required=True, help='Event title')
        add.add_argument('--type', required=True,
                        choices=[t.value for t in EventType],
                        help='Event type')
        add.add_argument('--date', '-d', required=True, help='Event date')
        add.add_argument('--time', help='Event time (HH:MM)')
        add.add_argument('--department', help='Department')
        add.add_argument('--create-deadlines', action='store_true',
                        help='Create associated deadlines')
        add.set_defaults(func=self._cmd_event_add)

        # event list
        list_cmd = event_sub.add_parser('list', help='List events for a case')
        list_cmd.add_argument('--case', '-c', required=True, help='Case number')
        list_cmd.add_argument('--upcoming-only', action='store_true',
                             help='Show only upcoming events')
        list_cmd.set_defaults(func=self._cmd_event_list)

        # event complete
        complete = event_sub.add_parser('complete', help='Record event result')
        complete.add_argument('event_id', help='Event ID')
        complete.add_argument('--result', '-r', required=True,
                             choices=[r.value for r in EventResult],
                             help='Event result')
        complete.add_argument('--summary', '-s', help='Ruling summary')
        complete.set_defaults(func=self._cmd_event_complete)

    def _add_calculate_commands(self, subparsers):
        """Add calculation commands."""
        calc_parser = subparsers.add_parser('calculate', help='Deadline calculation commands')
        calc_sub = calc_parser.add_subparsers(dest='calc_command')

        # calculate deadline
        deadline = calc_sub.add_parser('deadline', help='Calculate a deadline')
        deadline.add_argument('--from', dest='from_date', required=True,
                             help='Starting date')
        deadline.add_argument('--days', '-d', type=int, required=True,
                             help='Number of days')
        deadline.add_argument('--service', '-s', default='electronic',
                             choices=[m.value for m in ServiceMethod],
                             help='Service method')
        deadline.add_argument('--court-days', action='store_true',
                             help='Count court days instead of calendar days')
        deadline.set_defaults(func=self._cmd_calculate_deadline)

        # calculate motion
        motion = calc_sub.add_parser('motion', help='Calculate motion deadlines')
        motion.add_argument('--hearing', '-h', required=True,
                           help='Hearing date')
        motion.add_argument('--msj', action='store_true',
                           help='Summary judgment motion')
        motion.set_defaults(func=self._cmd_calculate_motion)

        # calculate discovery
        discovery = calc_sub.add_parser('discovery', help='Calculate discovery response deadline')
        discovery.add_argument('--served', '-s', required=True,
                              help='Service date')
        discovery.add_argument('--type', '-t', required=True,
                              choices=['interrogatories', 'rfp', 'rfa', 'deposition'],
                              help='Discovery type')
        discovery.add_argument('--method', '-m', default='electronic',
                              choices=[m.value for m in ServiceMethod],
                              help='Service method')
        discovery.set_defaults(func=self._cmd_calculate_discovery)

    def _add_report_commands(self, subparsers):
        """Add report commands."""
        report_parser = subparsers.add_parser('report', help='Generate reports')
        report_sub = report_parser.add_subparsers(dest='report_command')

        # report case
        case_report = report_sub.add_parser('case', help='Generate case report')
        case_report.add_argument('case_number', help='Case number')
        case_report.set_defaults(func=self._cmd_report_case)

        # report calendar
        cal_report = report_sub.add_parser('calendar', help='Generate calendar report')
        cal_report.add_argument('--case', '-c', required=True, help='Case number')
        cal_report.add_argument('--days', '-d', type=int, default=60,
                               help='Days ahead to include')
        cal_report.set_defaults(func=self._cmd_report_calendar)

        # report deadlines
        dl_report = report_sub.add_parser('deadlines', help='Generate deadline report')
        dl_report.add_argument('--case', '-c', help='Case number (omit for all cases)')
        dl_report.add_argument('--days', '-d', type=int, default=30,
                              help='Days ahead to include')
        dl_report.set_defaults(func=self._cmd_report_deadlines)

    # =========================================================================
    # Command Implementations
    # =========================================================================

    def _cmd_case_create(self, args):
        """Create a new case."""
        filing_date = parse_date(args.filed) if args.filed else None
        trial_date = parse_date(args.trial) if args.trial else None

        case = self.manager.create_case(
            case_number=args.number,
            case_name=args.name,
            case_type=CaseType(args.type),
            court_name=args.court,
            county=args.county,
            department=args.department,
            judge_name=args.judge,
            filing_date=filing_date,
            trial_date=trial_date
        )

        self.manager.save()
        print(f"Created case: {case.case_number}")
        print(f"  Name: {case.case_name}")
        print(f"  ID: {case.id}")

    def _cmd_case_list(self, args):
        """List all cases."""
        status = CaseStatus(args.status) if args.status else None
        cases = self.manager.list_cases(status)

        if not cases:
            print("No cases found.")
            return

        print(f"{'Case Number':<20} {'Case Name':<35} {'Status':<12} {'County'}")
        print("-" * 85)

        for case in cases:
            print(f"{case.case_number:<20} {case.case_name[:35]:<35} {case.status.value:<12} {case.county}")

    def _cmd_case_show(self, args):
        """Show case details."""
        case = self.manager.get_case_by_number(args.case_number)
        if not case:
            print(f"Case not found: {args.case_number}")
            return

        print(self.manager.generate_case_report(case.id))

    def _cmd_case_update(self, args):
        """Update case information."""
        case = self.manager.get_case_by_number(args.case_number)
        if not case:
            print(f"Case not found: {args.case_number}")
            return

        updates = {}
        if args.status:
            updates['status'] = CaseStatus(args.status)
        if args.department:
            updates['department'] = args.department
        if args.judge:
            updates['judge_name'] = args.judge
        if args.trial:
            updates['trial_date'] = parse_date(args.trial)

        if updates:
            self.manager.update_case(case.id, **updates)
            self.manager.save()
            print(f"Updated case: {case.case_number}")
        else:
            print("No updates specified.")

    def _cmd_party_add(self, args):
        """Add a party to a case."""
        case = self.manager.get_case_by_number(args.case)
        if not case:
            print(f"Case not found: {args.case}")
            return

        party = self.manager.add_party(
            case_id=case.id,
            name=args.name,
            party_type=PartyType(args.type),
            email=args.email,
            phone=args.phone
        )

        if args.attorney:
            self.manager.add_attorney_to_party(party.id, args.attorney)

        self.manager.save()
        print(f"Added party: {party.name} ({party.party_type.value})")

    def _cmd_party_list(self, args):
        """List parties for a case."""
        case = self.manager.get_case_by_number(args.case)
        if not case:
            print(f"Case not found: {args.case}")
            return

        parties = self.manager.get_case_parties(case.id)
        if not parties:
            print("No parties found.")
            return

        print(f"Parties in {case.case_number}:")
        print("-" * 60)

        for party in parties:
            print(f"  {party.party_type.value.upper()}: {party.name}")
            if party.attorneys:
                for atty in party.attorneys:
                    print(f"    Attorney: {atty.name}")
            if party.email:
                print(f"    Email: {party.email}")

    def _cmd_document_file(self, args):
        """Record a filed document."""
        case = self.manager.get_case_by_number(args.case)
        if not case:
            print(f"Case not found: {args.case}")
            return

        filing_date = parse_date(args.date)
        if not filing_date:
            print(f"Invalid date: {args.date}")
            return

        # Find party if specified
        filed_by_party_id = None
        if args.party:
            parties = self.manager.get_case_parties(case.id)
            for party in parties:
                if args.party.lower() in party.name.lower():
                    filed_by_party_id = party.id
                    break

        hearing_date = parse_date(args.hearing) if args.hearing else None

        document = self.manager.file_document(
            case_id=case.id,
            title=args.title,
            document_type=DocumentType(args.type),
            filing_date=filing_date,
            filed_by_party_id=filed_by_party_id,
            hearing_date=hearing_date
        )

        self.manager.save()
        print(f"Filed document: {document.title}")
        print(f"  ID: {document.id}")

    def _cmd_document_list(self, args):
        """List documents for a case."""
        case = self.manager.get_case_by_number(args.case)
        if not case:
            print(f"Case not found: {args.case}")
            return

        documents = self.manager.filing_tracker.get_case_documents(case.id)

        if args.type:
            documents = [d for d in documents if d.document_type.value == args.type]

        documents = documents[:args.limit]

        if not documents:
            print("No documents found.")
            return

        print(f"Documents in {case.case_number}:")
        print("-" * 80)

        for doc in documents:
            date_str = format_date(doc.filing_date) if doc.filing_date else "Not filed"
            print(f"  {date_str}  {doc.document_type.value:<15} {doc.title[:50]}")
            print(f"             ID: {doc.id}")

    def _cmd_document_serve(self, args):
        """Record service of a document."""
        document = self.manager.filing_tracker.get_document(args.document)
        if not document:
            print(f"Document not found: {args.document}")
            return

        service_date = parse_date(args.date)
        if not service_date:
            print(f"Invalid date: {args.date}")
            return

        # Find party
        parties = self.manager.get_case_parties(document.case_id)
        party = None
        for p in parties:
            if args.party.lower() in p.name.lower():
                party = p
                break

        if not party:
            print(f"Party not found: {args.party}")
            return

        self.manager.serve_document(
            document_id=document.id,
            party_id=party.id,
            service_method=ServiceMethod(args.method),
            service_date=service_date
        )

        self.manager.save()
        print(f"Recorded service on {party.name}")

    def _cmd_deadline_list(self, args):
        """List deadlines for a case."""
        case = self.manager.get_case_by_number(args.case)
        if not case:
            print(f"Case not found: {args.case}")
            return

        status = DeadlineStatus(args.status) if args.status else None
        deadlines = self.manager.get_case_deadlines(
            case.id,
            status=status,
            include_completed=args.include_completed
        )

        if not deadlines:
            print("No deadlines found.")
            return

        print(f"Deadlines for {case.case_number}:")
        print("-" * 80)

        for dl in deadlines:
            status_str = dl.get_status_display()
            print(f"  {format_date(dl.due_date)}  {dl.title}")
            print(f"             Status: {status_str}")
            print(f"             ID: {dl.id}")
            print()

    def _cmd_deadline_upcoming(self, args):
        """Show upcoming deadlines across all cases."""
        upcoming = self.manager.get_all_upcoming_deadlines(args.days)

        if not upcoming:
            print(f"No deadlines in the next {args.days} days.")
            return

        print(f"Upcoming Deadlines (next {args.days} days):")
        print("=" * 80)

        for case, deadline in upcoming:
            relative = format_relative_date(deadline.due_date)
            print(f"  {format_date(deadline.due_date)} ({relative})")
            print(f"    Case: {case.case_number}")
            print(f"    Deadline: {deadline.title}")
            print(f"    ID: {deadline.id}")
            print()

    def _cmd_deadline_complete(self, args):
        """Mark a deadline as completed."""
        success = self.manager.complete_deadline(args.deadline_id)
        if success:
            self.manager.save()
            print("Deadline marked as completed.")
        else:
            print(f"Deadline not found: {args.deadline_id}")

    def _cmd_deadline_extend(self, args):
        """Extend a deadline."""
        new_date = parse_date(args.date)
        if not new_date:
            print(f"Invalid date: {args.date}")
            return

        success = self.manager.extend_deadline(
            args.deadline_id,
            new_date=new_date,
            reason=args.reason,
            stipulated=args.stipulated,
            court_ordered=args.court_ordered
        )

        if success:
            self.manager.save()
            print(f"Deadline extended to {format_date(new_date)}")
        else:
            print(f"Deadline not found: {args.deadline_id}")

    def _cmd_event_add(self, args):
        """Add a calendar event."""
        case = self.manager.get_case_by_number(args.case)
        if not case:
            print(f"Case not found: {args.case}")
            return

        event_date = parse_date(args.date)
        if not event_date:
            print(f"Invalid date: {args.date}")
            return

        event_time = None
        if args.time:
            try:
                event_time = datetime.strptime(args.time, '%H:%M').time()
            except ValueError:
                print(f"Invalid time format: {args.time}")
                return

        event, deadlines = self.manager.schedule_hearing(
            case_id=case.id,
            title=args.title,
            hearing_date=event_date,
            event_type=EventType(args.type),
            event_time=event_time,
            department=args.department,
            create_deadlines=args.create_deadlines
        )

        self.manager.save()
        print(f"Created event: {event.title}")
        print(f"  Date: {format_date(event.event_date)}")
        print(f"  ID: {event.id}")

        if deadlines:
            print(f"  Created {len(deadlines)} associated deadlines")

    def _cmd_event_list(self, args):
        """List events for a case."""
        case = self.manager.get_case_by_number(args.case)
        if not case:
            print(f"Case not found: {args.case}")
            return

        events = self.manager.calendar_tracker.get_case_events(
            case.id,
            include_past=not args.upcoming_only
        )

        if not events:
            print("No events found.")
            return

        print(f"Events for {case.case_number}:")
        print("-" * 80)

        for event in events:
            time_str = event.get_display_time()
            location = event.get_display_location()
            status = event.status.value

            print(f"  {format_date(event.event_date)} {time_str}")
            print(f"    {event.title}")
            print(f"    Type: {event.event_type.value}")
            print(f"    Location: {location}")
            print(f"    Status: {status}")
            print(f"    ID: {event.id}")
            print()

    def _cmd_event_complete(self, args):
        """Record event result."""
        success = self.manager.complete_hearing(
            args.event_id,
            result=EventResult(args.result),
            ruling_summary=args.summary
        )

        if success:
            self.manager.save()
            print(f"Recorded result: {args.result}")
        else:
            print(f"Event not found: {args.event_id}")

    def _cmd_calculate_deadline(self, args):
        """Calculate a deadline."""
        from_date = parse_date(args.from_date)
        if not from_date:
            print(f"Invalid date: {args.from_date}")
            return

        service_method = ServiceMethod(args.service)

        deadline = self.manager.calculate_deadline(
            trigger_date=from_date,
            base_days=args.days,
            service_method=service_method,
            court_days=args.court_days
        )

        service_ext = self.manager.deadline_calculator.get_service_extension(service_method)

        print(f"Deadline Calculation:")
        print(f"  From date: {format_date(from_date)}")
        print(f"  Base days: {args.days}")
        print(f"  Service method: {service_method.value}")
        print(f"  Service extension: {service_ext} days")
        print(f"  Court days: {'Yes' if args.court_days else 'No'}")
        print(f"  Deadline: {format_date(deadline)} ({format_relative_date(deadline)})")

    def _cmd_calculate_motion(self, args):
        """Calculate motion deadlines."""
        hearing_date = parse_date(args.hearing)
        if not hearing_date:
            print(f"Invalid date: {args.hearing}")
            return

        if args.msj:
            deadlines = self.manager.deadline_calculator.calculate_msj_deadlines(hearing_date)
            print("Summary Judgment Motion Deadlines:")
        else:
            deadlines = self.manager.deadline_calculator.calculate_motion_deadlines(hearing_date)
            print("Motion Deadlines:")

        print(f"  Hearing Date: {format_date(hearing_date)}")
        print("-" * 50)
        print(f"  Moving Papers: {format_date(deadlines['moving_papers_deadline'])}")
        print(f"  Opposition:    {format_date(deadlines['opposition_deadline'])}")
        print(f"  Reply:         {format_date(deadlines['reply_deadline'])}")
        print(f"  Authority: {deadlines.get('ccp_section', 'CCP 1005(b)')}")

    def _cmd_calculate_discovery(self, args):
        """Calculate discovery response deadline."""
        served_date = parse_date(args.served)
        if not served_date:
            print(f"Invalid date: {args.served}")
            return

        doc_type_map = {
            'interrogatories': DocumentType.INTERROGATORIES,
            'rfp': DocumentType.REQUESTS_FOR_PRODUCTION,
            'rfa': DocumentType.REQUESTS_FOR_ADMISSION,
            'deposition': DocumentType.DEPOSITION_NOTICE,
        }

        doc_type = doc_type_map[args.type]
        service_method = ServiceMethod(args.method)

        deadline, ccp = self.manager.deadline_calculator.calculate_discovery_response_deadline(
            discovery_type=doc_type,
            service_date=served_date,
            service_method=service_method
        )

        print(f"Discovery Response Deadline:")
        print(f"  Service Date: {format_date(served_date)}")
        print(f"  Discovery Type: {args.type}")
        print(f"  Service Method: {service_method.value}")
        print(f"  Response Due: {format_date(deadline)} ({format_relative_date(deadline)})")
        print(f"  Authority: {ccp}")

    def _cmd_report_case(self, args):
        """Generate case report."""
        case = self.manager.get_case_by_number(args.case_number)
        if not case:
            print(f"Case not found: {args.case_number}")
            return

        print(self.manager.generate_case_report(case.id))

    def _cmd_report_calendar(self, args):
        """Generate calendar report."""
        case = self.manager.get_case_by_number(args.case)
        if not case:
            print(f"Case not found: {args.case}")
            return

        print(self.manager.calendar_tracker.generate_calendar_report(case.id, args.days))

    def _cmd_report_deadlines(self, args):
        """Generate deadline report."""
        if args.case:
            case = self.manager.get_case_by_number(args.case)
            if not case:
                print(f"Case not found: {args.case}")
                return
            deadlines = [(case, d) for d in self.manager.get_case_deadlines(case.id)]
        else:
            deadlines = self.manager.get_all_upcoming_deadlines(args.days)

        if not deadlines:
            print("No deadlines found.")
            return

        print("DEADLINE REPORT")
        print("=" * 80)
        print(f"Generated: {datetime.now().strftime('%m/%d/%Y %H:%M')}")
        print()

        for case, deadline in deadlines:
            status = deadline.get_status_display()
            print(f"  {format_date(deadline.due_date)} - {deadline.title}")
            print(f"    Case: {case.case_number}")
            print(f"    Status: {status}")
            if deadline.responsible_party_name:
                print(f"    Responsible: {deadline.responsible_party_name}")
            print()


def main():
    """Main entry point for the CLI."""
    cli = CourtTrackerCLI()
    cli.run()


if __name__ == '__main__':
    main()
