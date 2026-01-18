# Box Discovery Skill for Claude Code
# Reads case files from Box.com and drafts discovery responses

__version__ = "1.0.0"
__author__ = "Claude Code Skill"

from .box_client import BoxClient, BoxFile, BoxClientError
from .case_parser import (
    CaseFileParser,
    CaseProfile,
    Document,
    DocumentType,
    Party,
    KeyFact,
    KeyDate,
    LegalClaim
)
from .discovery_generator import (
    DiscoveryGenerator,
    DiscoveryType,
    DiscoverySet,
    DiscoveryResponseSet,
    DiscoveryRequest,
    DiscoveryResponse,
    PartyRole
)
from .skill import BoxDiscoverySkill, SkillConfig
from .local_adapter import LocalFileAdapter, create_local_skill

__all__ = [
    # Main skill
    "BoxDiscoverySkill",
    "SkillConfig",

    # Box client
    "BoxClient",
    "BoxFile",
    "BoxClientError",

    # Case parsing
    "CaseFileParser",
    "CaseProfile",
    "Document",
    "DocumentType",
    "Party",
    "KeyFact",
    "KeyDate",
    "LegalClaim",

    # Discovery generation
    "DiscoveryGenerator",
    "DiscoveryType",
    "DiscoverySet",
    "DiscoveryResponseSet",
    "DiscoveryRequest",
    "DiscoveryResponse",
    "PartyRole",

    # Local adapter
    "LocalFileAdapter",
    "create_local_skill",
]
