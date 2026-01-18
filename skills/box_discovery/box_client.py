"""
Box.com API Client for Case File Access

Provides secure access to Box.com files using OAuth 2.0 authentication.
Supports reading various document formats common in legal case files.
"""

import os
import json
import base64
import tempfile
from typing import Optional, Dict, List, Any, Union
from dataclasses import dataclass
from datetime import datetime
import urllib.request
import urllib.parse
import urllib.error
import ssl


@dataclass
class BoxFile:
    """Represents a file in Box.com"""
    id: str
    name: str
    size: int
    created_at: str
    modified_at: str
    parent_id: Optional[str] = None
    extension: Optional[str] = None
    content_type: Optional[str] = None

    @property
    def is_document(self) -> bool:
        """Check if file is a document type"""
        doc_extensions = {'.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt'}
        if self.extension:
            return self.extension.lower() in doc_extensions
        return False


@dataclass
class BoxFolder:
    """Represents a folder in Box.com"""
    id: str
    name: str
    created_at: str
    modified_at: str
    parent_id: Optional[str] = None
    item_count: int = 0


class BoxClientError(Exception):
    """Custom exception for Box API errors"""
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


class BoxClient:
    """
    Box.com API Client

    Authentication Options:
    1. Developer Token (for testing): Set BOX_DEVELOPER_TOKEN env var
    2. OAuth 2.0 (for production): Set BOX_CLIENT_ID, BOX_CLIENT_SECRET, BOX_ACCESS_TOKEN
    3. JWT (for server-to-server): Set BOX_JWT_CONFIG_PATH

    Example:
        client = BoxClient()
        files = client.list_folder("0")  # List root folder
        content = client.get_file_content("12345")
    """

    BASE_URL = "https://api.box.com/2.0"
    UPLOAD_URL = "https://upload.box.com/api/2.0"
    AUTH_URL = "https://account.box.com/api/oauth2"

    def __init__(
        self,
        access_token: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        developer_token: Optional[str] = None
    ):
        """
        Initialize Box client with authentication credentials.

        Args:
            access_token: OAuth 2.0 access token
            client_id: OAuth 2.0 client ID
            client_secret: OAuth 2.0 client secret
            developer_token: Developer token for testing (expires in 1 hour)
        """
        self.access_token = (
            access_token or
            developer_token or
            os.environ.get('BOX_ACCESS_TOKEN') or
            os.environ.get('BOX_DEVELOPER_TOKEN')
        )
        self.client_id = client_id or os.environ.get('BOX_CLIENT_ID')
        self.client_secret = client_secret or os.environ.get('BOX_CLIENT_SECRET')

        if not self.access_token:
            raise BoxClientError(
                "No Box authentication provided. Set BOX_ACCESS_TOKEN or "
                "BOX_DEVELOPER_TOKEN environment variable."
            )

        # Create SSL context
        self._ssl_context = ssl.create_default_context()

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        base_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Make authenticated request to Box API"""

        url = (base_url or self.BASE_URL) + endpoint

        if params:
            url += "?" + urllib.parse.urlencode(params)

        req_headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        if headers:
            req_headers.update(headers)

        body = None
        if data:
            body = json.dumps(data).encode('utf-8')

        request = urllib.request.Request(
            url,
            data=body,
            headers=req_headers,
            method=method
        )

        try:
            with urllib.request.urlopen(request, context=self._ssl_context) as response:
                response_data = response.read().decode('utf-8')
                if response_data:
                    return json.loads(response_data)
                return {}
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8') if e.fp else str(e)
            raise BoxClientError(
                f"Box API error: {error_body}",
                status_code=e.code
            )
        except urllib.error.URLError as e:
            raise BoxClientError(f"Network error: {str(e)}")

    def get_current_user(self) -> Dict[str, Any]:
        """Get the current authenticated user's information"""
        return self._make_request("GET", "/users/me")

    def list_folder(
        self,
        folder_id: str = "0",
        limit: int = 100,
        offset: int = 0,
        fields: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        List items in a folder.

        Args:
            folder_id: Box folder ID ("0" for root)
            limit: Maximum number of items to return
            offset: Offset for pagination
            fields: Specific fields to include

        Returns:
            Dict with folder items and metadata
        """
        params = {"limit": limit, "offset": offset}
        if fields:
            params["fields"] = ",".join(fields)

        return self._make_request(
            "GET",
            f"/folders/{folder_id}/items",
            params=params
        )

    def get_folder_info(self, folder_id: str) -> BoxFolder:
        """Get folder metadata"""
        data = self._make_request("GET", f"/folders/{folder_id}")
        return BoxFolder(
            id=data["id"],
            name=data["name"],
            created_at=data.get("created_at", ""),
            modified_at=data.get("modified_at", ""),
            parent_id=data.get("parent", {}).get("id"),
            item_count=data.get("item_collection", {}).get("total_count", 0)
        )

    def get_file_info(self, file_id: str) -> BoxFile:
        """Get file metadata"""
        data = self._make_request("GET", f"/files/{file_id}")
        name = data["name"]
        extension = os.path.splitext(name)[1] if name else None

        return BoxFile(
            id=data["id"],
            name=name,
            size=data.get("size", 0),
            created_at=data.get("created_at", ""),
            modified_at=data.get("modified_at", ""),
            parent_id=data.get("parent", {}).get("id"),
            extension=extension,
            content_type=data.get("content_type")
        )

    def get_file_content(self, file_id: str) -> bytes:
        """
        Download file content as bytes.

        Args:
            file_id: Box file ID

        Returns:
            File content as bytes
        """
        url = f"{self.BASE_URL}/files/{file_id}/content"

        request = urllib.request.Request(
            url,
            headers={"Authorization": f"Bearer {self.access_token}"},
            method="GET"
        )

        try:
            with urllib.request.urlopen(request, context=self._ssl_context) as response:
                return response.read()
        except urllib.error.HTTPError as e:
            raise BoxClientError(
                f"Failed to download file: {e}",
                status_code=e.code
            )

    def get_file_text_content(self, file_id: str) -> str:
        """
        Get extracted text content from a file.
        Uses Box's text representation API for supported formats.

        Args:
            file_id: Box file ID

        Returns:
            Extracted text content
        """
        # Try to get text representation
        try:
            params = {"fields": "representations"}
            file_info = self._make_request(
                "GET",
                f"/files/{file_id}",
                params=params,
                headers={"X-Rep-Hints": "[extracted_text]"}
            )

            representations = file_info.get("representations", {}).get("entries", [])
            for rep in representations:
                if rep.get("representation") == "extracted_text":
                    content_url = rep.get("content", {}).get("url_template", "")
                    if content_url:
                        content_url = content_url.replace("{+asset_path}", "")
                        request = urllib.request.Request(
                            content_url,
                            headers={"Authorization": f"Bearer {self.access_token}"},
                            method="GET"
                        )
                        with urllib.request.urlopen(request, context=self._ssl_context) as response:
                            return response.read().decode('utf-8')
        except Exception:
            pass

        # Fallback: download and try to decode as text
        content = self.get_file_content(file_id)
        try:
            return content.decode('utf-8')
        except UnicodeDecodeError:
            return content.decode('latin-1')

    def search_files(
        self,
        query: str,
        folder_ids: Optional[List[str]] = None,
        file_extensions: Optional[List[str]] = None,
        content_types: Optional[List[str]] = None,
        limit: int = 30
    ) -> List[BoxFile]:
        """
        Search for files in Box.

        Args:
            query: Search query string
            folder_ids: Limit search to specific folders
            file_extensions: Filter by file extensions
            content_types: Filter by content types
            limit: Maximum results to return

        Returns:
            List of matching BoxFile objects
        """
        params = {"query": query, "limit": limit}

        if folder_ids:
            params["ancestor_folder_ids"] = ",".join(folder_ids)
        if file_extensions:
            params["file_extensions"] = ",".join(file_extensions)
        if content_types:
            params["content_types"] = ",".join(content_types)

        result = self._make_request("GET", "/search", params=params)

        files = []
        for entry in result.get("entries", []):
            if entry.get("type") == "file":
                name = entry["name"]
                files.append(BoxFile(
                    id=entry["id"],
                    name=name,
                    size=entry.get("size", 0),
                    created_at=entry.get("created_at", ""),
                    modified_at=entry.get("modified_at", ""),
                    parent_id=entry.get("parent", {}).get("id"),
                    extension=os.path.splitext(name)[1] if name else None
                ))

        return files

    def get_shared_link_item(self, shared_link: str, password: Optional[str] = None) -> Dict[str, Any]:
        """
        Access an item via shared link.

        Args:
            shared_link: Box shared link URL
            password: Password if link is password-protected

        Returns:
            Item metadata
        """
        headers = {"BoxApi": f"shared_link={shared_link}"}
        if password:
            headers["BoxApi"] += f"&shared_link_password={password}"

        return self._make_request(
            "GET",
            "/shared_items",
            headers=headers
        )

    def download_file_to_path(self, file_id: str, destination_path: str) -> str:
        """
        Download a file to a local path.

        Args:
            file_id: Box file ID
            destination_path: Local file path to save to

        Returns:
            Path to downloaded file
        """
        content = self.get_file_content(file_id)

        # Ensure directory exists
        os.makedirs(os.path.dirname(destination_path), exist_ok=True)

        with open(destination_path, 'wb') as f:
            f.write(content)

        return destination_path

    def download_folder_contents(
        self,
        folder_id: str,
        destination_dir: str,
        recursive: bool = True,
        file_extensions: Optional[List[str]] = None
    ) -> List[str]:
        """
        Download all files from a folder.

        Args:
            folder_id: Box folder ID
            destination_dir: Local directory to save files
            recursive: Whether to download subfolders
            file_extensions: Only download files with these extensions

        Returns:
            List of paths to downloaded files
        """
        downloaded_files = []

        items = self.list_folder(folder_id, limit=1000)

        for entry in items.get("entries", []):
            if entry["type"] == "file":
                name = entry["name"]
                ext = os.path.splitext(name)[1].lower()

                if file_extensions and ext not in file_extensions:
                    continue

                dest_path = os.path.join(destination_dir, name)
                self.download_file_to_path(entry["id"], dest_path)
                downloaded_files.append(dest_path)

            elif entry["type"] == "folder" and recursive:
                subfolder_path = os.path.join(destination_dir, entry["name"])
                os.makedirs(subfolder_path, exist_ok=True)

                subfiles = self.download_folder_contents(
                    entry["id"],
                    subfolder_path,
                    recursive=True,
                    file_extensions=file_extensions
                )
                downloaded_files.extend(subfiles)

        return downloaded_files


def create_box_client_from_env() -> BoxClient:
    """
    Factory function to create BoxClient from environment variables.

    Required env vars (one of):
    - BOX_DEVELOPER_TOKEN: For quick testing (expires in 1 hour)
    - BOX_ACCESS_TOKEN: OAuth 2.0 access token

    Returns:
        Configured BoxClient instance
    """
    return BoxClient()
