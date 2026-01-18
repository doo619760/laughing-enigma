"""
Discovery Generator

Generates and answers legal discovery requests based on case file analysis.
Supports interrogatories, requests for production, and requests for admission.
"""

import os
import re
from typing import Optional, Dict, List, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from .case_parser import CaseProfile, KeyFact, Document, DocumentType


class DiscoveryType(Enum):
    """Types of discovery requests"""
    INTERROGATORY = "interrogatory"
    REQUEST_FOR_PRODUCTION = "request_for_production"
    REQUEST_FOR_ADMISSION = "request_for_admission"


class PartyRole(Enum):
    """Role of party generating/answering discovery"""
    PLAINTIFF = "plaintiff"
    DEFENDANT = "defendant"


@dataclass
class DiscoveryRequest:
    """A single discovery request"""
    number: int
    request_type: DiscoveryType
    text: str
    category: Optional[str] = None
    rationale: Optional[str] = None


@dataclass
class DiscoveryResponse:
    """Response to a discovery request"""
    request_number: int
    request_text: str
    response_text: str
    objections: List[str] = field(default_factory=list)
    documents_referenced: List[str] = field(default_factory=list)


@dataclass
class DiscoverySet:
    """A complete set of discovery requests"""
    title: str
    propounding_party: str
    responding_party: str
    discovery_type: DiscoveryType
    requests: List[DiscoveryRequest] = field(default_factory=list)
    preamble: str = ""
    definitions: str = ""
    instructions: str = ""

    def to_document(self) -> str:
        """Convert to formatted document text"""
        doc = []
        doc.append(self.title.upper())
        doc.append("")
        doc.append(f"PROPOUNDING PARTY: {self.propounding_party}")
        doc.append(f"RESPONDING PARTY: {self.responding_party}")
        doc.append("")

        if self.definitions:
            doc.append("DEFINITIONS")
            doc.append("")
            doc.append(self.definitions)
            doc.append("")

        if self.instructions:
            doc.append("INSTRUCTIONS")
            doc.append("")
            doc.append(self.instructions)
            doc.append("")

        type_label = self.discovery_type.value.replace("_", " ").upper()
        doc.append(f"{type_label}S")
        doc.append("")

        for req in self.requests:
            doc.append(f"{type_label} NO. {req.number}:")
            doc.append("")
            doc.append(req.text)
            doc.append("")

        return "\n".join(doc)


@dataclass
class DiscoveryResponseSet:
    """A complete set of discovery responses"""
    title: str
    propounding_party: str
    responding_party: str
    discovery_type: DiscoveryType
    responses: List[DiscoveryResponse] = field(default_factory=list)
    general_objections: List[str] = field(default_factory=list)

    def to_document(self) -> str:
        """Convert to formatted document text"""
        doc = []
        doc.append(self.title.upper())
        doc.append("")
        doc.append(f"PROPOUNDING PARTY: {self.propounding_party}")
        doc.append(f"RESPONDING PARTY: {self.responding_party}")
        doc.append("")

        if self.general_objections:
            doc.append("GENERAL OBJECTIONS")
            doc.append("")
            for i, obj in enumerate(self.general_objections, 1):
                doc.append(f"{i}. {obj}")
            doc.append("")
            doc.append("Subject to and without waiving these General Objections, ")
            doc.append(f"{self.responding_party} responds as follows:")
            doc.append("")

        type_label = self.discovery_type.value.replace("_", " ").upper()

        for resp in self.responses:
            doc.append(f"{type_label} NO. {resp.request_number}:")
            doc.append("")
            doc.append(resp.request_text)
            doc.append("")
            doc.append("RESPONSE:")
            doc.append("")

            if resp.objections:
                doc.append("OBJECTIONS: " + "; ".join(resp.objections))
                doc.append("")
                doc.append("Subject to and without waiving these objections, ")
                doc.append(f"{self.responding_party} responds as follows:")
                doc.append("")

            doc.append(resp.response_text)

            if resp.documents_referenced:
                doc.append("")
                doc.append("See documents: " + ", ".join(resp.documents_referenced))

            doc.append("")

        return "\n".join(doc)


class DiscoveryGenerator:
    """
    Generates discovery requests and responses based on case analysis.

    Supports:
    - Interrogatories (questions requiring written answers under oath)
    - Requests for Production (demands for documents/tangible items)
    - Requests for Admission (requests to admit or deny facts)
    """

    # Standard discovery templates
    STANDARD_INTERROGATORIES = {
        "identity": [
            "State your full legal name, all other names you have used, your date of birth, and your current address.",
            "Identify all persons who have knowledge of the facts alleged in the complaint and for each person state: (a) their name; (b) their address; (c) their telephone number; (d) their relationship to you; and (e) a summary of the information they possess.",
        ],
        "incident": [
            "Describe in detail your version of the events that are the subject of this lawsuit, including the date, time, location, and all persons present.",
            "State whether you made any statements, written or oral, regarding the incident alleged in the complaint, and if so, identify to whom each statement was made, when it was made, and the substance of each statement.",
        ],
        "documents": [
            "Identify all documents that you contend support your claims or defenses in this action, including the title of each document, its date, author, and current location.",
            "Identify all documents you reviewed or relied upon in preparing your responses to these interrogatories.",
        ],
        "damages": [
            "If you are claiming monetary damages, state the total amount claimed and itemize each element of damages with specificity.",
            "Identify all medical treatment you received related to the claims in this lawsuit, including: (a) the name and address of each healthcare provider; (b) the dates of treatment; and (c) the total amount billed and paid for each treatment.",
            "Identify all insurance coverage that may provide coverage for the claims alleged in this lawsuit.",
        ],
        "expert": [
            "Identify each expert witness you intend to call at trial and for each expert state: (a) their name and address; (b) their qualifications; (c) the subject matter of their expected testimony; and (d) the compensation they will receive.",
        ],
        "communications": [
            "Identify all communications between you and any party to this lawsuit regarding the subject matter of this litigation.",
            "Identify all communications with any government agency regarding the subject matter of this lawsuit.",
        ]
    }

    STANDARD_RFP_CATEGORIES = {
        "documents": [
            "All documents identified in your responses to interrogatories.",
            "All contracts, agreements, or writings between the parties.",
            "All correspondence between the parties regarding the subject matter of this lawsuit.",
        ],
        "communications": [
            "All emails, text messages, and electronic communications regarding the subject matter of this lawsuit.",
            "All written or recorded statements by any party or witness regarding the events at issue.",
        ],
        "financial": [
            "All documents evidencing or relating to any damages claimed in this lawsuit.",
            "All invoices, receipts, bills, and payment records related to the claims in this lawsuit.",
            "All financial statements, tax returns, or accounting records relevant to damages claimed.",
        ],
        "photographs": [
            "All photographs, videos, or other visual recordings of the incident or subject matter of this lawsuit.",
            "All photographs or documentation of any injuries or damages claimed.",
        ],
        "medical": [
            "All medical records related to injuries claimed in this lawsuit.",
            "All medical bills, invoices, and records of payment for medical treatment.",
        ],
        "expert": [
            "All reports, analyses, or documents prepared by any expert witness.",
            "All documents provided to or reviewed by any expert witness.",
        ],
        "insurance": [
            "All insurance policies that may provide coverage for the claims in this lawsuit.",
            "All correspondence with insurance companies regarding the claims in this lawsuit.",
        ]
    }

    STANDARD_RFA_CATEGORIES = {
        "identity": [
            "Admit that you are the {party_role} in this action.",
            "Admit that you were present at the time and place of the incident alleged in the complaint.",
        ],
        "documents": [
            "Admit that the document attached hereto as Exhibit {exhibit} is authentic.",
            "Admit that you authored the document attached as Exhibit {exhibit}.",
            "Admit that you received the document attached as Exhibit {exhibit}.",
        ],
        "facts": [
            "Admit that you entered into a contract with {opposing_party}.",
            "Admit that you breached the terms of the contract.",
            "Admit that {opposing_party} performed all obligations under the contract.",
        ],
        "damages": [
            "Admit that {opposing_party} suffered damages as a result of your conduct.",
            "Admit that the damages claimed by {opposing_party} are reasonable.",
        ]
    }

    COMMON_OBJECTIONS = {
        "vague": "This request is vague, ambiguous, and fails to describe with reasonable particularity the information or documents sought.",
        "overbroad": "This request is overbroad in scope and seeks information that is not relevant to any claim or defense in this action.",
        "unduly_burdensome": "This request is unduly burdensome and oppressive, requiring {responding_party} to engage in extensive investigation and review disproportionate to the needs of this case.",
        "privilege": "{Responding_party} objects to this request to the extent it seeks information protected by the attorney-client privilege, work product doctrine, or any other applicable privilege.",
        "proprietary": "This request seeks confidential, proprietary, or trade secret information. Any response is subject to an appropriate protective order.",
        "not_relevant": "This request seeks information that is not relevant to any party's claim or defense and is not proportional to the needs of this case.",
        "compound": "This request is compound and contains multiple subparts. {Responding_party} will respond to each subpart to the extent identifiable.",
        "speculation": "This request calls for speculation and is impossible to answer with certainty.",
        "premature": "This request is premature as discovery is ongoing and all relevant documents and information have not yet been identified.",
        "equally_available": "The information requested is equally available to the propounding party through its own investigation.",
    }

    GENERAL_OBJECTIONS_TEMPLATE = [
        "{Responding_party} objects to each request to the extent it seeks information protected by the attorney-client privilege, work product doctrine, or any other applicable privilege or immunity from discovery.",
        "{Responding_party} objects to each request to the extent it is vague, ambiguous, overly broad, unduly burdensome, or seeks information not relevant to any claim or defense in this action.",
        "{Responding_party} objects to each request to the extent it seeks confidential, proprietary, or trade secret information without adequate protections.",
        "{Responding_party} reserves the right to supplement these responses as additional information becomes available through ongoing investigation and discovery.",
    ]

    DEFINITIONS_TEMPLATE = """
As used herein, the following terms shall have the meanings set forth below:

1. "DOCUMENT" means any writing or recording of any type, including but not limited to correspondence, memoranda, notes, emails, text messages, reports, studies, summaries, contracts, agreements, photographs, videos, recordings, and electronically stored information.

2. "IDENTIFY" when used with respect to a person means to state the person's full name, present or last known address, telephone number, and relationship to any party.

3. "IDENTIFY" when used with respect to a document means to state the document's title, date, author, recipient(s), and current custodian or location.

4. "RELATING TO" or "CONCERNING" means referring to, reflecting, evidencing, describing, constituting, or being in any way pertinent to the subject matter.

5. "YOU" and "YOUR" refer to the responding party and any agents, representatives, employees, or attorneys acting on their behalf.

6. "COMMUNICATION" means any transmission or exchange of information, whether oral, written, or electronic.
"""

    INSTRUCTIONS_TEMPLATE = """
In responding to these {discovery_type}, you are instructed as follows:

1. If you object to any {discovery_type_singular}, state the grounds for your objection with specificity.

2. If you withhold any information based on a claim of privilege, identify the information withheld and the privilege claimed.

3. If you lack sufficient information to fully respond, so state and provide whatever information you do possess.

4. These {discovery_type} are continuing in nature. You are required to supplement your responses if additional responsive information becomes available.

5. If any document has been lost, destroyed, or is otherwise unavailable, identify the document and explain the circumstances of its unavailability.
"""

    def __init__(self, case_profile: CaseProfile, client_role: PartyRole = PartyRole.PLAINTIFF):
        """
        Initialize discovery generator with case profile.

        Args:
            case_profile: Parsed case profile
            client_role: Role of the client (plaintiff or defendant)
        """
        self.case_profile = case_profile
        self.client_role = client_role

        # Determine party names
        if client_role == PartyRole.PLAINTIFF:
            self.client_name = case_profile.plaintiffs[0].name if case_profile.plaintiffs else "Plaintiff"
            self.opposing_name = case_profile.defendants[0].name if case_profile.defendants else "Defendant"
        else:
            self.client_name = case_profile.defendants[0].name if case_profile.defendants else "Defendant"
            self.opposing_name = case_profile.plaintiffs[0].name if case_profile.plaintiffs else "Plaintiff"

    def generate_interrogatories(
        self,
        categories: Optional[List[str]] = None,
        custom_interrogatories: Optional[List[str]] = None,
        max_count: int = 25
    ) -> DiscoverySet:
        """
        Generate a set of interrogatories.

        Args:
            categories: Categories of interrogatories to include
            custom_interrogatories: Additional custom interrogatories
            max_count: Maximum number of interrogatories (jurisdictional limit)

        Returns:
            DiscoverySet with formatted interrogatories
        """
        if categories is None:
            categories = list(self.STANDARD_INTERROGATORIES.keys())

        requests = []
        number = 1

        # Add standard interrogatories by category
        for category in categories:
            if category in self.STANDARD_INTERROGATORIES and number <= max_count:
                for template in self.STANDARD_INTERROGATORIES[category]:
                    if number > max_count:
                        break
                    text = self._personalize_template(template)
                    requests.append(DiscoveryRequest(
                        number=number,
                        request_type=DiscoveryType.INTERROGATORY,
                        text=text,
                        category=category
                    ))
                    number += 1

        # Add case-specific interrogatories based on claims
        for claim in self.case_profile.legal_claims[:3]:
            if number > max_count:
                break
            text = f"Describe all facts supporting your contention that {claim.claim_type.lower()}."
            requests.append(DiscoveryRequest(
                number=number,
                request_type=DiscoveryType.INTERROGATORY,
                text=text,
                category="claims"
            ))
            number += 1

        # Add custom interrogatories
        if custom_interrogatories:
            for custom in custom_interrogatories:
                if number > max_count:
                    break
                requests.append(DiscoveryRequest(
                    number=number,
                    request_type=DiscoveryType.INTERROGATORY,
                    text=custom,
                    category="custom"
                ))
                number += 1

        # Build discovery set
        title = f"{self.client_name.upper()}'S FIRST SET OF INTERROGATORIES TO {self.opposing_name.upper()}"

        return DiscoverySet(
            title=title,
            propounding_party=self.client_name,
            responding_party=self.opposing_name,
            discovery_type=DiscoveryType.INTERROGATORY,
            requests=requests,
            definitions=self.DEFINITIONS_TEMPLATE,
            instructions=self.INSTRUCTIONS_TEMPLATE.format(
                discovery_type="interrogatories",
                discovery_type_singular="interrogatory"
            )
        )

    def generate_requests_for_production(
        self,
        categories: Optional[List[str]] = None,
        custom_requests: Optional[List[str]] = None,
    ) -> DiscoverySet:
        """
        Generate requests for production of documents.

        Args:
            categories: Categories of documents to request
            custom_requests: Additional custom requests

        Returns:
            DiscoverySet with formatted RFPs
        """
        if categories is None:
            categories = list(self.STANDARD_RFP_CATEGORIES.keys())

        requests = []
        number = 1

        for category in categories:
            if category in self.STANDARD_RFP_CATEGORIES:
                for template in self.STANDARD_RFP_CATEGORIES[category]:
                    text = self._personalize_template(template)
                    requests.append(DiscoveryRequest(
                        number=number,
                        request_type=DiscoveryType.REQUEST_FOR_PRODUCTION,
                        text=text,
                        category=category
                    ))
                    number += 1

        # Add document-specific requests based on documents in case profile
        for doc in self.case_profile.documents:
            if doc.document_type in [DocumentType.CONTRACT, DocumentType.CORRESPONDENCE]:
                text = f"All documents relating to or referencing {doc.title or doc.filename}."
                requests.append(DiscoveryRequest(
                    number=number,
                    request_type=DiscoveryType.REQUEST_FOR_PRODUCTION,
                    text=text,
                    category="case_specific"
                ))
                number += 1

        # Add custom requests
        if custom_requests:
            for custom in custom_requests:
                requests.append(DiscoveryRequest(
                    number=number,
                    request_type=DiscoveryType.REQUEST_FOR_PRODUCTION,
                    text=custom,
                    category="custom"
                ))
                number += 1

        title = f"{self.client_name.upper()}'S FIRST REQUEST FOR PRODUCTION OF DOCUMENTS TO {self.opposing_name.upper()}"

        return DiscoverySet(
            title=title,
            propounding_party=self.client_name,
            responding_party=self.opposing_name,
            discovery_type=DiscoveryType.REQUEST_FOR_PRODUCTION,
            requests=requests,
            definitions=self.DEFINITIONS_TEMPLATE,
            instructions=self.INSTRUCTIONS_TEMPLATE.format(
                discovery_type="requests for production",
                discovery_type_singular="request"
            )
        )

    def generate_requests_for_admission(
        self,
        facts_to_admit: Optional[List[str]] = None,
        documents_to_authenticate: Optional[List[str]] = None,
    ) -> DiscoverySet:
        """
        Generate requests for admission.

        Args:
            facts_to_admit: Specific facts to request admission of
            documents_to_authenticate: Documents to authenticate

        Returns:
            DiscoverySet with formatted RFAs
        """
        requests = []
        number = 1

        # Standard identity admissions
        for template in self.STANDARD_RFA_CATEGORIES["identity"]:
            text = self._personalize_template(template)
            requests.append(DiscoveryRequest(
                number=number,
                request_type=DiscoveryType.REQUEST_FOR_ADMISSION,
                text=text,
                category="identity"
            ))
            number += 1

        # Document authentication
        if documents_to_authenticate:
            for i, doc in enumerate(documents_to_authenticate, 1):
                text = f"Admit that the document attached hereto as Exhibit {chr(64+i)} ({doc}) is authentic."
                requests.append(DiscoveryRequest(
                    number=number,
                    request_type=DiscoveryType.REQUEST_FOR_ADMISSION,
                    text=text,
                    category="documents"
                ))
                number += 1

        # Key facts from case profile
        for fact in self.case_profile.key_facts[:10]:
            if not fact.disputed:
                text = f"Admit that {fact.fact}"
                requests.append(DiscoveryRequest(
                    number=number,
                    request_type=DiscoveryType.REQUEST_FOR_ADMISSION,
                    text=text,
                    category="facts"
                ))
                number += 1

        # Custom facts to admit
        if facts_to_admit:
            for fact in facts_to_admit:
                text = f"Admit that {fact}"
                requests.append(DiscoveryRequest(
                    number=number,
                    request_type=DiscoveryType.REQUEST_FOR_ADMISSION,
                    text=text,
                    category="custom"
                ))
                number += 1

        title = f"{self.client_name.upper()}'S FIRST REQUESTS FOR ADMISSION TO {self.opposing_name.upper()}"

        return DiscoverySet(
            title=title,
            propounding_party=self.client_name,
            responding_party=self.opposing_name,
            discovery_type=DiscoveryType.REQUEST_FOR_ADMISSION,
            requests=requests,
            definitions=self.DEFINITIONS_TEMPLATE,
            instructions=self.INSTRUCTIONS_TEMPLATE.format(
                discovery_type="requests for admission",
                discovery_type_singular="request"
            )
        )

    def draft_interrogatory_responses(
        self,
        interrogatories: List[Tuple[int, str]],
        provide_objections: bool = True
    ) -> DiscoveryResponseSet:
        """
        Draft responses to interrogatories based on case file.

        Args:
            interrogatories: List of (number, text) tuples
            provide_objections: Whether to include standard objections

        Returns:
            DiscoveryResponseSet with drafted responses
        """
        responses = []

        for number, text in interrogatories:
            response = self._draft_single_interrogatory_response(number, text)
            if provide_objections:
                response.objections = self._determine_objections(text)
            responses.append(response)

        general_objections = []
        if provide_objections:
            general_objections = [
                obj.format(
                    Responding_party=self.client_name,
                    responding_party=self.client_name.lower()
                )
                for obj in self.GENERAL_OBJECTIONS_TEMPLATE
            ]

        title = f"{self.client_name.upper()}'S RESPONSES TO {self.opposing_name.upper()}'S INTERROGATORIES"

        return DiscoveryResponseSet(
            title=title,
            propounding_party=self.opposing_name,
            responding_party=self.client_name,
            discovery_type=DiscoveryType.INTERROGATORY,
            responses=responses,
            general_objections=general_objections
        )

    def draft_rfp_responses(
        self,
        requests: List[Tuple[int, str]],
        provide_objections: bool = True
    ) -> DiscoveryResponseSet:
        """
        Draft responses to requests for production.

        Args:
            requests: List of (number, text) tuples
            provide_objections: Whether to include standard objections

        Returns:
            DiscoveryResponseSet with drafted responses
        """
        responses = []

        for number, text in requests:
            response = self._draft_single_rfp_response(number, text)
            if provide_objections:
                response.objections = self._determine_objections(text)
            responses.append(response)

        general_objections = []
        if provide_objections:
            general_objections = [
                obj.format(
                    Responding_party=self.client_name,
                    responding_party=self.client_name.lower()
                )
                for obj in self.GENERAL_OBJECTIONS_TEMPLATE
            ]

        title = f"{self.client_name.upper()}'S RESPONSES TO {self.opposing_name.upper()}'S REQUESTS FOR PRODUCTION"

        return DiscoveryResponseSet(
            title=title,
            propounding_party=self.opposing_name,
            responding_party=self.client_name,
            discovery_type=DiscoveryType.REQUEST_FOR_PRODUCTION,
            responses=responses,
            general_objections=general_objections
        )

    def draft_rfa_responses(
        self,
        requests: List[Tuple[int, str]],
    ) -> DiscoveryResponseSet:
        """
        Draft responses to requests for admission.

        Args:
            requests: List of (number, text) tuples

        Returns:
            DiscoveryResponseSet with drafted responses
        """
        responses = []

        for number, text in requests:
            response = self._draft_single_rfa_response(number, text)
            responses.append(response)

        title = f"{self.client_name.upper()}'S RESPONSES TO {self.opposing_name.upper()}'S REQUESTS FOR ADMISSION"

        return DiscoveryResponseSet(
            title=title,
            propounding_party=self.opposing_name,
            responding_party=self.client_name,
            discovery_type=DiscoveryType.REQUEST_FOR_ADMISSION,
            responses=responses
        )

    def _draft_single_interrogatory_response(self, number: int, text: str) -> DiscoveryResponse:
        """Draft response to a single interrogatory"""
        text_lower = text.lower()

        # Default response template
        response_text = f"{self.client_name} responds as follows:\n\n"

        # Try to match interrogatory type and provide appropriate response
        if "identify" in text_lower and "person" in text_lower:
            # Request to identify persons
            parties = []
            for p in self.case_profile.plaintiffs + self.case_profile.defendants:
                parties.append(p.name)
            if parties:
                response_text += f"The following persons have knowledge of relevant facts: {', '.join(parties)}. "
                response_text += "Investigation is ongoing and this response will be supplemented."
            else:
                response_text += "Investigation is ongoing. This response will be supplemented when additional information becomes available."

        elif "describe" in text_lower and ("event" in text_lower or "incident" in text_lower):
            # Request to describe events
            facts = [f.fact for f in self.case_profile.key_facts[:5]]
            if facts:
                response_text += "Based on available information, the relevant facts are as follows:\n\n"
                for i, fact in enumerate(facts, 1):
                    response_text += f"{i}. {fact}\n"
            else:
                response_text += "Investigation is ongoing. A detailed description will be provided upon completion of discovery."

        elif "document" in text_lower:
            # Request about documents
            docs = [d.filename for d in self.case_profile.documents[:10]]
            if docs:
                response_text += f"The following documents are relevant to this matter: {', '.join(docs)}. "
                response_text += "Additional documents may be identified through ongoing discovery."
            else:
                response_text += "Responsive documents will be identified and produced in accordance with the applicable rules."

        elif "damage" in text_lower:
            # Damages interrogatory
            response_text += f"{self.client_name} is still evaluating damages. "
            response_text += "This response will be supplemented with specific damage calculations upon completion of expert analysis and discovery."

        elif "expert" in text_lower:
            # Expert witness interrogatory
            response_text += f"{self.client_name} has not yet retained expert witnesses. "
            response_text += "Expert disclosures will be made in accordance with the applicable scheduling order."

        else:
            # Generic response
            response_text += "Investigation is ongoing. A complete response will be provided upon completion of discovery and investigation."

        return DiscoveryResponse(
            request_number=number,
            request_text=text,
            response_text=response_text
        )

    def _draft_single_rfp_response(self, number: int, text: str) -> DiscoveryResponse:
        """Draft response to a single RFP"""
        text_lower = text.lower()

        # Find potentially responsive documents
        responsive_docs = []
        for doc in self.case_profile.documents:
            doc_name_lower = doc.filename.lower()
            # Simple keyword matching
            keywords = re.findall(r'\b\w{4,}\b', text_lower)
            for keyword in keywords:
                if keyword in doc_name_lower or (doc.summary and keyword in doc.summary.lower()):
                    responsive_docs.append(doc.filename)
                    break

        response_text = f"{self.client_name} responds as follows:\n\n"

        if responsive_docs:
            response_text += f"Subject to the objections stated, {self.client_name} will produce the following responsive documents: "
            response_text += ", ".join(responsive_docs[:10])
            response_text += ".\n\n{self.client_name} reserves the right to supplement this response."
        else:
            response_text += f"After reasonable inquiry, {self.client_name} is not aware of documents responsive to this request. "
            response_text += f"{self.client_name} will supplement this response if responsive documents are identified."

        return DiscoveryResponse(
            request_number=number,
            request_text=text,
            response_text=response_text,
            documents_referenced=responsive_docs[:10]
        )

    def _draft_single_rfa_response(self, number: int, text: str) -> DiscoveryResponse:
        """Draft response to a single RFA"""
        text_lower = text.lower()

        # Check if fact matches known facts
        for fact in self.case_profile.key_facts:
            if fact.fact.lower() in text_lower or text_lower in fact.fact.lower():
                if not fact.disputed:
                    return DiscoveryResponse(
                        request_number=number,
                        request_text=text,
                        response_text="Admitted."
                    )
                else:
                    return DiscoveryResponse(
                        request_number=number,
                        request_text=text,
                        response_text="Denied."
                    )

        # Check for document authentication
        if "authentic" in text_lower or "exhibit" in text_lower:
            for doc in self.case_profile.documents:
                if doc.filename.lower() in text_lower:
                    return DiscoveryResponse(
                        request_number=number,
                        request_text=text,
                        response_text="Admitted that the document is authentic."
                    )

        # Default response
        return DiscoveryResponse(
            request_number=number,
            request_text=text,
            response_text=f"{self.client_name} lacks sufficient information to admit or deny this request and therefore denies the same."
        )

    def _determine_objections(self, text: str) -> List[str]:
        """Determine applicable objections for a discovery request"""
        objections = []
        text_lower = text.lower()

        # Check for vague/ambiguous terms
        vague_terms = ['any', 'all', 'each', 'every', 'relating to', 'concerning', 'regarding']
        if any(term in text_lower for term in vague_terms):
            objections.append(self.COMMON_OBJECTIONS["vague"].format(
                responding_party=self.client_name.lower(),
                Responding_party=self.client_name
            ))

        # Check for overbroad requests
        broad_indicators = ['all documents', 'all communications', 'any and all', 'each and every']
        if any(indicator in text_lower for indicator in broad_indicators):
            objections.append(self.COMMON_OBJECTIONS["overbroad"].format(
                responding_party=self.client_name.lower(),
                Responding_party=self.client_name
            ))

        # Always include privilege objection for document requests
        if 'document' in text_lower or 'communication' in text_lower:
            objections.append(self.COMMON_OBJECTIONS["privilege"].format(
                responding_party=self.client_name.lower(),
                Responding_party=self.client_name
            ))

        return objections[:3]  # Limit to 3 most relevant objections

    def _personalize_template(self, template: str) -> str:
        """Replace template placeholders with case-specific values"""
        replacements = {
            '{party_role}': self.client_role.value,
            '{opposing_party}': self.opposing_name,
            '{client}': self.client_name,
        }
        result = template
        for placeholder, value in replacements.items():
            result = result.replace(placeholder, value)
        return result


def create_discovery_generator(case_profile: CaseProfile, role: str = "plaintiff") -> DiscoveryGenerator:
    """
    Factory function to create a DiscoveryGenerator.

    Args:
        case_profile: Parsed case profile
        role: Client role ("plaintiff" or "defendant")

    Returns:
        Configured DiscoveryGenerator
    """
    party_role = PartyRole.PLAINTIFF if role.lower() == "plaintiff" else PartyRole.DEFENDANT
    return DiscoveryGenerator(case_profile, party_role)
