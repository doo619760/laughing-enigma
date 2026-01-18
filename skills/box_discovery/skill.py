#!/usr/bin/env python3
"""
Box Discovery Skill for Claude Code

Main entry point for the discovery drafting skill. This skill:
1. Connects to Box.com to read case files
2. Parses documents to build a case profile
3. Generates discovery requests or drafts responses

Usage:
    # As a module
    from skills.box_discovery import BoxDiscoverySkill
    skill = BoxDiscoverySkill()
    skill.process_case_folder("folder_id")

    # CLI
    python -m skills.box_discovery.skill --folder-id 123456 --action generate

Environment Variables Required:
    BOX_ACCESS_TOKEN or BOX_DEVELOPER_TOKEN: Box.com authentication token

"""

import os
import sys
import json
import argparse
import tempfile
from typing import Optional, Dict, List, Any, Tuple
from dataclasses import dataclass

from .box_client import BoxClient, BoxFile, BoxClientError
from .case_parser import CaseFileParser, CaseProfile, DocumentType
from .discovery_generator import (
    DiscoveryGenerator,
    DiscoveryType,
    PartyRole,
    DiscoverySet,
    DiscoveryResponseSet
)


@dataclass
class SkillConfig:
    """Configuration for the Box Discovery Skill"""
    box_folder_id: Optional[str] = None
    box_file_id: Optional[str] = None
    box_shared_link: Optional[str] = None
    client_role: str = "plaintiff"  # plaintiff or defendant
    output_format: str = "text"  # text, json, or markdown
    output_path: Optional[str] = None
    action: str = "analyze"  # analyze, generate_interrogatories, generate_rfp, generate_rfa, respond


class BoxDiscoverySkill:
    """
    Claude Code Skill for legal discovery using Box.com case files.

    This skill reads case files from Box.com, analyzes them to extract
    relevant information, and generates or responds to discovery requests.
    """

    SUPPORTED_EXTENSIONS = {'.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt'}

    def __init__(self, config: Optional[SkillConfig] = None):
        """
        Initialize the skill.

        Args:
            config: Skill configuration (uses defaults if not provided)
        """
        self.config = config or SkillConfig()
        self.box_client: Optional[BoxClient] = None
        self.parser = CaseFileParser()
        self.case_profile: Optional[CaseProfile] = None
        self.generator: Optional[DiscoveryGenerator] = None

    def initialize_box_client(self) -> BoxClient:
        """Initialize and return the Box.com client"""
        if self.box_client is None:
            self.box_client = BoxClient()
        return self.box_client

    def load_case_from_folder(self, folder_id: str) -> CaseProfile:
        """
        Load and parse all case files from a Box folder.

        Args:
            folder_id: Box folder ID containing case files

        Returns:
            Parsed CaseProfile
        """
        client = self.initialize_box_client()

        # List folder contents
        items = client.list_folder(folder_id, limit=100)
        documents = []

        for entry in items.get("entries", []):
            if entry["type"] == "file":
                name = entry["name"]
                ext = os.path.splitext(name)[1].lower()

                if ext in self.SUPPORTED_EXTENSIONS:
                    print(f"Processing: {name}")
                    try:
                        content = client.get_file_text_content(entry["id"])
                        documents.append((content, name, entry["id"]))
                    except Exception as e:
                        print(f"Warning: Could not read {name}: {e}")

        if not documents:
            raise ValueError(f"No supported documents found in folder {folder_id}")

        # Parse all documents
        self.case_profile = self.parser.parse_case_file(documents)

        # Initialize generator
        role = PartyRole.PLAINTIFF if self.config.client_role.lower() == "plaintiff" else PartyRole.DEFENDANT
        self.generator = DiscoveryGenerator(self.case_profile, role)

        return self.case_profile

    def load_case_from_file(self, file_id: str) -> CaseProfile:
        """
        Load and parse a single case file from Box.

        Args:
            file_id: Box file ID

        Returns:
            Parsed CaseProfile
        """
        client = self.initialize_box_client()

        file_info = client.get_file_info(file_id)
        content = client.get_file_text_content(file_id)

        documents = [(content, file_info.name, file_id)]
        self.case_profile = self.parser.parse_case_file(documents)

        role = PartyRole.PLAINTIFF if self.config.client_role.lower() == "plaintiff" else PartyRole.DEFENDANT
        self.generator = DiscoveryGenerator(self.case_profile, role)

        return self.case_profile

    def load_case_from_shared_link(self, shared_link: str, password: Optional[str] = None) -> CaseProfile:
        """
        Load case files from a Box shared link.

        Args:
            shared_link: Box shared link URL
            password: Optional password for protected links

        Returns:
            Parsed CaseProfile
        """
        client = self.initialize_box_client()

        item = client.get_shared_link_item(shared_link, password)

        if item.get("type") == "folder":
            return self.load_case_from_folder(item["id"])
        elif item.get("type") == "file":
            return self.load_case_from_file(item["id"])
        else:
            raise ValueError(f"Unsupported item type: {item.get('type')}")

    def analyze_case(self) -> Dict[str, Any]:
        """
        Analyze the loaded case and return structured information.

        Returns:
            Dictionary with case analysis
        """
        if not self.case_profile:
            raise ValueError("No case loaded. Call load_case_* first.")

        return self.parser.get_discovery_context()

    def generate_interrogatories(
        self,
        categories: Optional[List[str]] = None,
        custom_questions: Optional[List[str]] = None,
        max_count: int = 25
    ) -> DiscoverySet:
        """
        Generate interrogatories for the opposing party.

        Args:
            categories: Categories to include (identity, incident, documents, damages, expert, communications)
            custom_questions: Additional custom interrogatories
            max_count: Maximum number of interrogatories

        Returns:
            DiscoverySet with formatted interrogatories
        """
        if not self.generator:
            raise ValueError("No case loaded. Call load_case_* first.")

        return self.generator.generate_interrogatories(
            categories=categories,
            custom_interrogatories=custom_questions,
            max_count=max_count
        )

    def generate_requests_for_production(
        self,
        categories: Optional[List[str]] = None,
        custom_requests: Optional[List[str]] = None
    ) -> DiscoverySet:
        """
        Generate requests for production of documents.

        Args:
            categories: Document categories to request
            custom_requests: Additional custom requests

        Returns:
            DiscoverySet with formatted RFPs
        """
        if not self.generator:
            raise ValueError("No case loaded. Call load_case_* first.")

        return self.generator.generate_requests_for_production(
            categories=categories,
            custom_requests=custom_requests
        )

    def generate_requests_for_admission(
        self,
        facts: Optional[List[str]] = None,
        documents: Optional[List[str]] = None
    ) -> DiscoverySet:
        """
        Generate requests for admission.

        Args:
            facts: Specific facts to request admission of
            documents: Documents to authenticate

        Returns:
            DiscoverySet with formatted RFAs
        """
        if not self.generator:
            raise ValueError("No case loaded. Call load_case_* first.")

        return self.generator.generate_requests_for_admission(
            facts_to_admit=facts,
            documents_to_authenticate=documents
        )

    def respond_to_interrogatories(
        self,
        interrogatories: List[Tuple[int, str]],
        include_objections: bool = True
    ) -> DiscoveryResponseSet:
        """
        Draft responses to interrogatories.

        Args:
            interrogatories: List of (number, text) tuples
            include_objections: Whether to include standard objections

        Returns:
            DiscoveryResponseSet with drafted responses
        """
        if not self.generator:
            raise ValueError("No case loaded. Call load_case_* first.")

        return self.generator.draft_interrogatory_responses(
            interrogatories=interrogatories,
            provide_objections=include_objections
        )

    def respond_to_rfp(
        self,
        requests: List[Tuple[int, str]],
        include_objections: bool = True
    ) -> DiscoveryResponseSet:
        """
        Draft responses to requests for production.

        Args:
            requests: List of (number, text) tuples
            include_objections: Whether to include standard objections

        Returns:
            DiscoveryResponseSet with drafted responses
        """
        if not self.generator:
            raise ValueError("No case loaded. Call load_case_* first.")

        return self.generator.draft_rfp_responses(
            requests=requests,
            provide_objections=include_objections
        )

    def respond_to_rfa(
        self,
        requests: List[Tuple[int, str]]
    ) -> DiscoveryResponseSet:
        """
        Draft responses to requests for admission.

        Args:
            requests: List of (number, text) tuples

        Returns:
            DiscoveryResponseSet with drafted responses
        """
        if not self.generator:
            raise ValueError("No case loaded. Call load_case_* first.")

        return self.generator.draft_rfa_responses(requests=requests)

    def get_case_summary(self) -> str:
        """
        Get a human-readable summary of the case.

        Returns:
            Formatted case summary string
        """
        if not self.case_profile:
            return "No case loaded."

        lines = []
        lines.append("=" * 60)
        lines.append("CASE SUMMARY")
        lines.append("=" * 60)

        if self.case_profile.case_number:
            lines.append(f"Case Number: {self.case_profile.case_number}")
        if self.case_profile.court:
            lines.append(f"Court: {self.case_profile.court}")

        lines.append("")
        lines.append("PARTIES")
        lines.append("-" * 30)

        if self.case_profile.plaintiffs:
            lines.append("Plaintiffs:")
            for p in self.case_profile.plaintiffs:
                lines.append(f"  - {p.name}")

        if self.case_profile.defendants:
            lines.append("Defendants:")
            for d in self.case_profile.defendants:
                lines.append(f"  - {d.name}")

        if self.case_profile.legal_claims:
            lines.append("")
            lines.append("CLAIMS")
            lines.append("-" * 30)
            for claim in self.case_profile.legal_claims:
                lines.append(f"  - {claim.claim_type}")

        if self.case_profile.key_dates:
            lines.append("")
            lines.append("KEY DATES")
            lines.append("-" * 30)
            for date in self.case_profile.key_dates[:10]:
                lines.append(f"  - {date.date}: {date.description}")

        lines.append("")
        lines.append("DOCUMENTS")
        lines.append("-" * 30)
        for doc in self.case_profile.documents:
            lines.append(f"  - [{doc.document_type.value.upper()}] {doc.filename}")

        if self.case_profile.key_facts:
            lines.append("")
            lines.append("KEY FACTS")
            lines.append("-" * 30)
            for fact in self.case_profile.key_facts[:10]:
                lines.append(f"  - {fact.fact[:100]}...")

        lines.append("")
        lines.append("=" * 60)

        return "\n".join(lines)

    def run(self) -> str:
        """
        Execute the skill based on configuration.

        Returns:
            Output string (formatted based on config.output_format)
        """
        # Load case files
        if self.config.box_shared_link:
            self.load_case_from_shared_link(self.config.box_shared_link)
        elif self.config.box_folder_id:
            self.load_case_from_folder(self.config.box_folder_id)
        elif self.config.box_file_id:
            self.load_case_from_file(self.config.box_file_id)
        else:
            raise ValueError("No Box source specified. Provide folder_id, file_id, or shared_link.")

        # Execute action
        action = self.config.action.lower()
        result = None

        if action == "analyze":
            if self.config.output_format == "json":
                result = json.dumps(self.analyze_case(), indent=2)
            else:
                result = self.get_case_summary()

        elif action == "generate_interrogatories":
            discovery_set = self.generate_interrogatories()
            result = discovery_set.to_document()

        elif action == "generate_rfp":
            discovery_set = self.generate_requests_for_production()
            result = discovery_set.to_document()

        elif action == "generate_rfa":
            discovery_set = self.generate_requests_for_admission()
            result = discovery_set.to_document()

        elif action == "generate_all":
            # Generate all types of discovery
            outputs = []
            outputs.append(self.generate_interrogatories().to_document())
            outputs.append("\n" + "=" * 60 + "\n")
            outputs.append(self.generate_requests_for_production().to_document())
            outputs.append("\n" + "=" * 60 + "\n")
            outputs.append(self.generate_requests_for_admission().to_document())
            result = "\n".join(outputs)

        else:
            raise ValueError(f"Unknown action: {action}")

        # Output result
        if self.config.output_path:
            with open(self.config.output_path, 'w') as f:
                f.write(result)
            return f"Output written to: {self.config.output_path}"

        return result


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Box Discovery Skill - Read case files from Box.com and draft discovery"
    )

    # Source options
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument(
        "--folder-id",
        help="Box folder ID containing case files"
    )
    source_group.add_argument(
        "--file-id",
        help="Box file ID of a single case file"
    )
    source_group.add_argument(
        "--shared-link",
        help="Box shared link URL"
    )

    # Action
    parser.add_argument(
        "--action",
        choices=["analyze", "generate_interrogatories", "generate_rfp", "generate_rfa", "generate_all"],
        default="analyze",
        help="Action to perform"
    )

    # Role
    parser.add_argument(
        "--role",
        choices=["plaintiff", "defendant"],
        default="plaintiff",
        help="Client's role in the case"
    )

    # Output
    parser.add_argument(
        "--output",
        help="Output file path (prints to stdout if not specified)"
    )
    parser.add_argument(
        "--format",
        choices=["text", "json", "markdown"],
        default="text",
        help="Output format"
    )

    args = parser.parse_args()

    # Build config
    config = SkillConfig(
        box_folder_id=args.folder_id,
        box_file_id=args.file_id,
        box_shared_link=args.shared_link,
        client_role=args.role,
        action=args.action,
        output_format=args.format,
        output_path=args.output
    )

    # Run skill
    skill = BoxDiscoverySkill(config)

    try:
        result = skill.run()
        print(result)
    except BoxClientError as e:
        print(f"Box API Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
