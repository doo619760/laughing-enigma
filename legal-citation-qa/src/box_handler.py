"""
Box webhook handler and file integration.
Handles Box API interactions for downloading files and uploading reports.
"""

from typing import Optional, Dict, Any
import logging
from pathlib import Path
import tempfile
import os

try:
    from boxsdk import Client, OAuth2
    from boxsdk.exception import BoxAPIException
    BOX_AVAILABLE = True
except ImportError:
    BOX_AVAILABLE = False
    Client = None
    OAuth2 = None
    BoxAPIException = Exception

logger = logging.getLogger(__name__)


class BoxHandler:
    """Handle Box file operations and webhooks."""

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        access_token: Optional[str] = None
    ):
        """
        Initialize Box handler.

        Args:
            client_id: Box app client ID
            client_secret: Box app client secret
            access_token: Box access token
        """
        if not BOX_AVAILABLE:
            logger.warning("boxsdk not installed - Box integration disabled")
            self.client = None
            return

        self.client_id = client_id or os.getenv('BOX_CLIENT_ID')
        self.client_secret = client_secret or os.getenv('BOX_CLIENT_SECRET')
        self.access_token = access_token or os.getenv('BOX_ACCESS_TOKEN')

        self.client = None

        if self.access_token:
            self._initialize_client()

    def _initialize_client(self):
        """Initialize Box client with authentication."""
        if not BOX_AVAILABLE:
            return

        try:
            # Simple token auth (for service account or developer token)
            if self.access_token:
                oauth = OAuth2(
                    client_id=self.client_id,
                    client_secret=self.client_secret,
                    access_token=self.access_token
                )
                self.client = Client(oauth)
                logger.info("Box client initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Box client: {e}")
            self.client = None

    def download_file(
        self,
        file_id: str,
        download_path: Optional[str] = None
    ) -> Optional[str]:
        """
        Download file from Box.

        Args:
            file_id: Box file ID
            download_path: Optional local path to save file.
                          If None, creates temp file.

        Returns:
            Path to downloaded file, or None on error
        """
        if not self.client:
            logger.error("Box client not initialized")
            return None

        try:
            # Get file info
            file_info = self.client.file(file_id).get()
            filename = file_info.name

            # Determine download path
            if not download_path:
                # Create temp file with same extension
                suffix = Path(filename).suffix
                temp_file = tempfile.NamedTemporaryFile(
                    delete=False,
                    suffix=suffix
                )
                download_path = temp_file.name
                temp_file.close()

            # Download file
            with open(download_path, 'wb') as f:
                self.client.file(file_id).download_to(f)

            logger.info(f"Downloaded Box file {file_id} to {download_path}")
            return download_path

        except BoxAPIException as e:
            logger.error(f"Box API error downloading file {file_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error downloading Box file {file_id}: {e}")
            return None

    def upload_file(
        self,
        file_path: str,
        folder_id: str,
        file_name: Optional[str] = None
    ) -> Optional[str]:
        """
        Upload file to Box folder.

        Args:
            file_path: Local file path
            folder_id: Box folder ID
            file_name: Optional filename (defaults to file_path basename)

        Returns:
            Box file ID, or None on error
        """
        if not self.client:
            logger.error("Box client not initialized")
            return None

        try:
            if not file_name:
                file_name = Path(file_path).name

            # Upload file
            folder = self.client.folder(folder_id)
            uploaded_file = folder.upload(file_path, file_name)

            logger.info(f"Uploaded {file_path} to Box folder {folder_id}")
            return uploaded_file.id

        except BoxAPIException as e:
            logger.error(f"Box API error uploading file: {e}")
            return None
        except Exception as e:
            logger.error(f"Error uploading file to Box: {e}")
            return None

    def get_file_info(self, file_id: str) -> Optional[Dict[str, Any]]:
        """
        Get file metadata from Box.

        Args:
            file_id: Box file ID

        Returns:
            File info dictionary, or None on error
        """
        if not self.client:
            logger.error("Box client not initialized")
            return None

        try:
            file_info = self.client.file(file_id).get()

            return {
                'id': file_info.id,
                'name': file_info.name,
                'size': file_info.size,
                'created_at': str(file_info.created_at),
                'modified_at': str(file_info.modified_at),
                'created_by': file_info.created_by.get('name') if file_info.created_by else None,
                'extension': file_info.extension,
                'path': file_info.path_collection.get('entries', [])
            }

        except BoxAPIException as e:
            logger.error(f"Box API error getting file info: {e}")
            return None
        except Exception as e:
            logger.error(f"Error getting Box file info: {e}")
            return None

    def create_folder(
        self,
        parent_folder_id: str,
        folder_name: str
    ) -> Optional[str]:
        """
        Create a folder in Box.

        Args:
            parent_folder_id: Parent folder ID
            folder_name: New folder name

        Returns:
            Created folder ID, or None on error
        """
        if not self.client:
            logger.error("Box client not initialized")
            return None

        try:
            parent_folder = self.client.folder(parent_folder_id)
            new_folder = parent_folder.create_subfolder(folder_name)

            logger.info(f"Created Box folder '{folder_name}' in {parent_folder_id}")
            return new_folder.id

        except BoxAPIException as e:
            if e.status == 409:
                # Folder already exists
                logger.info(f"Folder '{folder_name}' already exists")
                # Try to get existing folder
                items = self.client.folder(parent_folder_id).get_items()
                for item in items:
                    if item.name == folder_name and item.type == 'folder':
                        return item.id
            logger.error(f"Box API error creating folder: {e}")
            return None
        except Exception as e:
            logger.error(f"Error creating Box folder: {e}")
            return None

    def verify_webhook_signature(
        self,
        payload: bytes,
        headers: Dict[str, str],
        webhook_signing_key: str
    ) -> bool:
        """
        Verify Box webhook signature.

        Args:
            payload: Raw webhook payload
            headers: Request headers
            webhook_signing_key: Box webhook signing key

        Returns:
            True if signature is valid
        """
        import hmac
        import hashlib

        # Get signature headers
        primary_sig = headers.get('Box-Signature-Primary', '')
        secondary_sig = headers.get('Box-Signature-Secondary', '')
        timestamp = headers.get('Box-Signature-Timestamp', '')
        algorithm = headers.get('Box-Signature-Algorithm', 'HmacSHA256')

        if not all([primary_sig, timestamp]):
            logger.warning("Missing required webhook signature headers")
            return False

        # Compute expected signature
        message = payload + timestamp.encode('utf-8')

        if algorithm == 'HmacSHA256':
            expected_sig = hmac.new(
                webhook_signing_key.encode('utf-8'),
                message,
                hashlib.sha256
            ).digest().hex()
        else:
            logger.warning(f"Unsupported signature algorithm: {algorithm}")
            return False

        # Compare signatures
        if hmac.compare_digest(expected_sig, primary_sig):
            return True
        if secondary_sig and hmac.compare_digest(expected_sig, secondary_sig):
            return True

        logger.warning("Webhook signature verification failed")
        return False

    def process_webhook_event(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process a Box webhook event.

        Args:
            event: Webhook event dictionary

        Returns:
            Processed event info, or None if not relevant
        """
        event_type = event.get('event_type')
        trigger = event.get('trigger')

        # We're interested in FILE.UPLOADED and FILE.COPIED events
        if event_type not in ['FILE.UPLOADED', 'FILE.COPIED']:
            logger.debug(f"Ignoring webhook event type: {event_type}")
            return None

        source = event.get('source', {})
        file_id = source.get('id')
        file_name = source.get('name')
        file_extension = source.get('extension')

        # Filter for .docx and .pdf files
        if file_extension not in ['docx', 'pdf']:
            logger.debug(f"Ignoring non-document file: {file_name}")
            return None

        return {
            'event_type': event_type,
            'file_id': file_id,
            'file_name': file_name,
            'file_extension': file_extension,
            'created_by': event.get('created_by', {}).get('name'),
            'created_at': event.get('created_at')
        }


class MockBoxHandler:
    """Mock Box handler for testing without Box credentials."""

    def __init__(self, *args, **kwargs):
        """Initialize mock handler."""
        logger.info("Using MockBoxHandler (no actual Box integration)")

    def download_file(self, file_id: str, download_path: Optional[str] = None) -> Optional[str]:
        """Mock download."""
        logger.info(f"Mock: Would download Box file {file_id}")
        return None

    def upload_file(self, file_path: str, folder_id: str, file_name: Optional[str] = None) -> Optional[str]:
        """Mock upload."""
        logger.info(f"Mock: Would upload {file_path} to Box folder {folder_id}")
        return "mock_file_id"

    def get_file_info(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Mock file info."""
        return {
            'id': file_id,
            'name': 'mock_file.docx',
            'size': 1024,
            'extension': 'docx'
        }

    def create_folder(self, parent_folder_id: str, folder_name: str) -> Optional[str]:
        """Mock folder creation."""
        logger.info(f"Mock: Would create folder '{folder_name}' in {parent_folder_id}")
        return "mock_folder_id"

    def verify_webhook_signature(self, payload: bytes, headers: Dict[str, str], webhook_signing_key: str) -> bool:
        """Mock signature verification."""
        return True

    def process_webhook_event(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Mock event processing."""
        return event
