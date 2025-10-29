"""
Git audit trail functionality.
Maintains an append-only audit log of QA reports in a git repository.
"""

from typing import Optional, Dict, Any
import logging
from pathlib import Path
from datetime import datetime
import json

try:
    from git import Repo, GitCommandError
    GIT_AVAILABLE = True
except ImportError:
    GIT_AVAILABLE = False
    Repo = None
    GitCommandError = Exception

logger = logging.getLogger(__name__)


class GitAuditTrail:
    """Maintain an append-only audit trail of QA reports in git."""

    def __init__(
        self,
        repo_path: str,
        remote_url: Optional[str] = None,
        branch: str = "main"
    ):
        """
        Initialize Git audit trail.

        Args:
            repo_path: Path to local git repository
            remote_url: Optional remote repository URL
            branch: Branch name (default: main)
        """
        if not GIT_AVAILABLE:
            logger.warning("GitPython not installed - Git audit disabled")
            self.repo = None
            return

        self.repo_path = Path(repo_path)
        self.remote_url = remote_url
        self.branch = branch
        self.repo = None

        # Initialize repository
        self._init_repository()

    def _init_repository(self):
        """Initialize or open git repository."""
        if not GIT_AVAILABLE:
            return

        try:
            if self.repo_path.exists() and (self.repo_path / '.git').exists():
                # Open existing repo
                self.repo = Repo(self.repo_path)
                logger.info(f"Opened existing git repository at {self.repo_path}")
            else:
                # Create new repo
                self.repo_path.mkdir(parents=True, exist_ok=True)
                self.repo = Repo.init(self.repo_path)
                logger.info(f"Initialized new git repository at {self.repo_path}")

                # Create initial commit
                readme_path = self.repo_path / 'README.md'
                readme_path.write_text(
                    "# Legal Citation QA Audit Trail\n\n"
                    "This repository contains an append-only audit log of "
                    "citation QA reports.\n\n"
                    "DO NOT modify or delete entries - this is an immutable audit trail.\n"
                )
                self.repo.index.add(['README.md'])
                self.repo.index.commit("Initial commit: Create audit trail repository")

            # Add remote if specified
            if self.remote_url and 'origin' not in self.repo.remotes:
                self.repo.create_remote('origin', self.remote_url)
                logger.info(f"Added remote 'origin': {self.remote_url}")

        except Exception as e:
            logger.error(f"Failed to initialize git repository: {e}")
            self.repo = None

    def commit_report(
        self,
        report: Dict[str, Any],
        document_name: str,
        report_json_path: Optional[str] = None,
        report_html_path: Optional[str] = None
    ) -> bool:
        """
        Commit a QA report to the audit trail.

        Args:
            report: Report dictionary
            document_name: Name of analyzed document
            report_json_path: Optional path to existing JSON report file
            report_html_path: Optional path to existing HTML report file

        Returns:
            True if successful
        """
        if not self.repo:
            logger.error("Git repository not initialized")
            return False

        try:
            # Create directory structure: YYYY/MM/DD/
            now = datetime.utcnow()
            date_dir = self.repo_path / str(now.year) / f"{now.month:02d}" / f"{now.day:02d}"
            date_dir.mkdir(parents=True, exist_ok=True)

            # Generate unique filename with timestamp
            timestamp = now.strftime("%H%M%S")
            safe_doc_name = self._sanitize_filename(document_name)
            base_name = f"{timestamp}_{safe_doc_name}"

            # Save JSON report
            json_path = date_dir / f"{base_name}.json"
            if report_json_path and Path(report_json_path).exists():
                # Copy existing file
                import shutil
                shutil.copy(report_json_path, json_path)
            else:
                # Save report dict as JSON
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(report, f, indent=2, ensure_ascii=False)

            # Save HTML report if provided
            html_path = None
            if report_html_path and Path(report_html_path).exists():
                html_path = date_dir / f"{base_name}.html"
                import shutil
                shutil.copy(report_html_path, html_path)

            # Add to git
            files_to_add = [str(json_path.relative_to(self.repo_path))]
            if html_path:
                files_to_add.append(str(html_path.relative_to(self.repo_path)))

            self.repo.index.add(files_to_add)

            # Create commit message
            commit_msg = self._generate_commit_message(report, document_name)

            # Commit
            self.repo.index.commit(commit_msg)

            logger.info(f"Committed QA report to audit trail: {json_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to commit report to git: {e}")
            return False

    def push_to_remote(self) -> bool:
        """
        Push commits to remote repository.

        Returns:
            True if successful
        """
        if not self.repo:
            logger.error("Git repository not initialized")
            return False

        if 'origin' not in self.repo.remotes:
            logger.error("No remote 'origin' configured")
            return False

        try:
            origin = self.repo.remotes.origin
            origin.push(refspec=f'{self.branch}:{self.branch}')

            logger.info(f"Pushed audit trail to remote: {self.remote_url}")
            return True

        except GitCommandError as e:
            logger.error(f"Failed to push to remote: {e}")
            return False
        except Exception as e:
            logger.error(f"Error pushing to remote: {e}")
            return False

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe use in filesystem."""
        # Remove extension
        name = Path(filename).stem

        # Replace unsafe characters
        safe = name.replace(' ', '_')
        safe = ''.join(c for c in safe if c.isalnum() or c in ('_', '-'))

        # Limit length
        return safe[:100]

    def _generate_commit_message(
        self,
        report: Dict[str, Any],
        document_name: str
    ) -> str:
        """Generate git commit message for report."""
        summary = report.get('summary', {})
        status = summary.get('overall_status', 'unknown')

        msg = f"QA Report: {document_name}\n\n"
        msg += f"Status: {status.upper()}\n"
        msg += f"Citations: {summary.get('total_citations', 0)}\n"
        msg += f"Quotes: {summary.get('total_quotes', 0)}\n"
        msg += f"Exact Matches: {summary.get('quotes_exact_match', 0)}\n"
        msg += f"Partial Matches: {summary.get('quotes_partial_match', 0)}\n"
        msg += f"No Match: {summary.get('quotes_no_match', 0)}\n"
        msg += f"Parallel Citation Issues: {summary.get('parallel_citations_issues', 0)}\n"
        msg += f"\nGenerated: {report.get('metadata', {}).get('generated_at', 'unknown')}\n"

        return msg

    def get_history(
        self,
        limit: int = 50,
        document_name: Optional[str] = None
    ) -> list:
        """
        Get audit trail history.

        Args:
            limit: Maximum number of commits to return
            document_name: Optional filter by document name

        Returns:
            List of commit info dictionaries
        """
        if not self.repo:
            logger.error("Git repository not initialized")
            return []

        try:
            commits = []

            for commit in self.repo.iter_commits(max_count=limit):
                commit_info = {
                    'sha': commit.hexsha,
                    'message': commit.message,
                    'author': str(commit.author),
                    'date': commit.committed_datetime.isoformat(),
                    'files': [item.a_path for item in commit.diff(commit.parents[0])] if commit.parents else []
                }

                # Filter by document name if specified
                if document_name:
                    if document_name.lower() not in commit.message.lower():
                        continue

                commits.append(commit_info)

            return commits

        except Exception as e:
            logger.error(f"Failed to get git history: {e}")
            return []

    def verify_integrity(self) -> Dict[str, Any]:
        """
        Verify integrity of audit trail.

        Returns:
            Dictionary with integrity check results
        """
        if not self.repo:
            return {'status': 'error', 'message': 'Git repository not initialized'}

        try:
            # Check if repo is dirty
            is_clean = not self.repo.is_dirty()

            # Count commits
            commit_count = sum(1 for _ in self.repo.iter_commits())

            # Count report files
            json_files = list(self.repo_path.glob('**/*.json'))
            json_count = len(json_files) - 1  # Exclude potential metadata files

            return {
                'status': 'ok',
                'is_clean': is_clean,
                'total_commits': commit_count,
                'total_reports': json_count,
                'branch': self.repo.active_branch.name,
                'last_commit': self.repo.head.commit.hexsha if commit_count > 0 else None
            }

        except Exception as e:
            logger.error(f"Integrity check failed: {e}")
            return {'status': 'error', 'message': str(e)}


class MockGitAuditTrail:
    """Mock Git audit trail for testing without git."""

    def __init__(self, *args, **kwargs):
        """Initialize mock audit trail."""
        logger.info("Using MockGitAuditTrail (no actual git integration)")

    def commit_report(
        self,
        report: Dict[str, Any],
        document_name: str,
        report_json_path: Optional[str] = None,
        report_html_path: Optional[str] = None
    ) -> bool:
        """Mock commit."""
        logger.info(f"Mock: Would commit report for {document_name}")
        return True

    def push_to_remote(self) -> bool:
        """Mock push."""
        logger.info("Mock: Would push to remote")
        return True

    def get_history(self, limit: int = 50, document_name: Optional[str] = None) -> list:
        """Mock history."""
        return []

    def verify_integrity(self) -> Dict[str, Any]:
        """Mock integrity check."""
        return {
            'status': 'ok',
            'is_clean': True,
            'total_commits': 0,
            'total_reports': 0
        }
