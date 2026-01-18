#!/usr/bin/env python3
"""
Interactive Example: Box Discovery Skill

This example shows how Claude Code can interactively use the Box Discovery skill
to analyze case files and draft discovery.
"""

import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from skills.box_discovery import BoxDiscoverySkill, SkillConfig
from skills.box_discovery.discovery_generator import DiscoveryType


def example_full_workflow():
    """
    Example: Complete discovery workflow

    This demonstrates:
    1. Loading case files from Box
    2. Analyzing the case
    3. Generating discovery requests
    4. Drafting responses to opposing party's discovery
    """

    print("=" * 60)
    print("BOX DISCOVERY SKILL - FULL WORKFLOW EXAMPLE")
    print("=" * 60)
    print()

    # Check for authentication
    if not os.environ.get('BOX_ACCESS_TOKEN') and not os.environ.get('BOX_DEVELOPER_TOKEN'):
        print("ERROR: Please set BOX_ACCESS_TOKEN or BOX_DEVELOPER_TOKEN environment variable")
        print()
        print("To get a developer token:")
        print("1. Go to https://developer.box.com/")
        print("2. Create or select your app")
        print("3. Generate a Developer Token")
        print("4. Run: export BOX_DEVELOPER_TOKEN='your_token_here'")
        return

    # Example folder ID (replace with your actual folder ID)
    FOLDER_ID = os.environ.get('BOX_FOLDER_ID', 'YOUR_FOLDER_ID')

    if FOLDER_ID == 'YOUR_FOLDER_ID':
        print("Set BOX_FOLDER_ID environment variable to your case folder ID")
        print("Example: export BOX_FOLDER_ID='123456789'")
        return

    # Initialize skill
    print("Initializing Box Discovery Skill...")
    skill = BoxDiscoverySkill()

    # Step 1: Load case files
    print(f"\n[1] Loading case files from folder {FOLDER_ID}...")
    try:
        case_profile = skill.load_case_from_folder(FOLDER_ID)
        print(f"    Loaded {len(case_profile.documents)} documents")
    except Exception as e:
        print(f"Error loading case: {e}")
        return

    # Step 2: Show case summary
    print("\n[2] Case Summary:")
    print("-" * 40)
    print(skill.get_case_summary())

    # Step 3: Generate interrogatories
    print("\n[3] Generating Interrogatories...")
    print("-" * 40)
    interrogatories = skill.generate_interrogatories(
        categories=["identity", "incident", "damages"],
        max_count=10
    )
    print(interrogatories.to_document()[:2000] + "...")

    # Step 4: Generate requests for production
    print("\n[4] Generating Requests for Production...")
    print("-" * 40)
    rfps = skill.generate_requests_for_production(
        categories=["documents", "communications"]
    )
    print(rfps.to_document()[:2000] + "...")

    # Step 5: Generate requests for admission
    print("\n[5] Generating Requests for Admission...")
    print("-" * 40)
    rfas = skill.generate_requests_for_admission()
    print(rfas.to_document()[:1500] + "...")

    # Step 6: Example of responding to opposing party's discovery
    print("\n[6] Drafting Responses to Sample Interrogatories...")
    print("-" * 40)

    # Sample opposing party interrogatories
    opposing_interrogatories = [
        (1, "State your full legal name, all aliases, date of birth, and current address."),
        (2, "Describe in complete detail the events giving rise to this lawsuit."),
        (3, "Identify all documents that support your claims in this action."),
        (4, "State the total amount of damages you claim and itemize each element."),
        (5, "Identify each expert witness you intend to call at trial."),
    ]

    responses = skill.respond_to_interrogatories(
        opposing_interrogatories,
        include_objections=True
    )
    print(responses.to_document()[:3000] + "...")

    print("\n" + "=" * 60)
    print("WORKFLOW COMPLETE")
    print("=" * 60)
    print("\nNote: All generated documents are drafts requiring attorney review.")


def example_analyze_only():
    """Simple example: Just analyze case files"""

    print("ANALYZE CASE EXAMPLE")
    print("-" * 40)

    # Using configuration
    config = SkillConfig(
        box_folder_id=os.environ.get('BOX_FOLDER_ID', '123456789'),
        action="analyze",
        output_format="text"
    )

    skill = BoxDiscoverySkill(config)

    try:
        result = skill.run()
        print(result)
    except Exception as e:
        print(f"Error: {e}")


def example_generate_discovery():
    """Example: Generate all discovery types"""

    print("GENERATE ALL DISCOVERY EXAMPLE")
    print("-" * 40)

    config = SkillConfig(
        box_folder_id=os.environ.get('BOX_FOLDER_ID', '123456789'),
        client_role="plaintiff",
        action="generate_all",
        output_path="discovery_output.txt"
    )

    skill = BoxDiscoverySkill(config)

    try:
        result = skill.run()
        print(result)
    except Exception as e:
        print(f"Error: {e}")


def example_respond_to_discovery():
    """Example: Respond to incoming discovery"""

    print("RESPOND TO DISCOVERY EXAMPLE")
    print("-" * 40)

    skill = BoxDiscoverySkill()

    # Load case
    folder_id = os.environ.get('BOX_FOLDER_ID', '123456789')
    skill.load_case_from_folder(folder_id)

    # Sample incoming RFPs from opposing party
    incoming_rfps = [
        (1, "All documents relating to the contract at issue in this litigation."),
        (2, "All communications between you and any defendant regarding the subject matter of this lawsuit."),
        (3, "All photographs or videos of the incident or damages claimed."),
    ]

    # Draft responses
    responses = skill.respond_to_rfp(incoming_rfps, include_objections=True)
    print(responses.to_document())


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Box Discovery Skill Examples")
    parser.add_argument(
        "--example",
        choices=["full", "analyze", "generate", "respond"],
        default="full",
        help="Which example to run"
    )

    args = parser.parse_args()

    if args.example == "full":
        example_full_workflow()
    elif args.example == "analyze":
        example_analyze_only()
    elif args.example == "generate":
        example_generate_discovery()
    elif args.example == "respond":
        example_respond_to_discovery()
