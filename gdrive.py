import os
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from typing import List, Dict, Optional

class GoogleDriveAPI:
    # def __init__(self, credentials_file: str = 'credentials.json', token_file: str = 'token.json'):
    def __init__(self, credentials_file: str = 'D:\\ltp\\mcp\\gdrive\\mcp-gdrive-py\\.config\\gcp-oauth.keys.json', token_file: str = 'D:\\ltp\\mcp\\gdrive\\mcp-gdrive-py\\.config\\tokens.json'):
        """
        Initialize Google Drive API client
        
        Args:
            credentials_file: Path to your OAuth2 credentials JSON file
            token_file: Path to store the access token
        """
        self.SCOPES = [
            'https://www.googleapis.com/auth/drive.readonly',
            'https://www.googleapis.com/auth/spreadsheets'
        ]
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        """Handle OAuth2 authentication"""
        creds = None
        
        print("process creds ...")
        # Load existing token if available
        if os.path.exists(self.token_file):
            creds = Credentials.from_authorized_user_file(self.token_file, self.SCOPES)
        # if os.path.exists(self.credentials_file):
        #     creds = Credentials.from_authorized_user_file(self.credentials_file, self.SCOPES)
        
        print('creds: ', creds)
        
        # If there are no valid credentials, request authorization
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    print(f"Error refreshing token: {e}")
                    creds = None
            
            if not creds:
                if not os.path.exists(self.credentials_file):
                    raise FileNotFoundError(f"Credentials file '{self.credentials_file}' not found!")
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, self.SCOPES
                )
                creds = flow.run_local_server(port=0)
            
            # Save credentials for next run
            with open(self.token_file, 'w') as token:
                token.write(creds.to_json())
        
        # Build the service
        self.service = build('drive', 'v3', credentials=creds)
        print("Successfully authenticated with Google Drive API!")
    
    def list_files(self, page_size: int = 10, folder_id: Optional[str] = None) -> List[Dict]:
        """
        List files in Google Drive
        
        Args:
            page_size: Number of files to return (max 1000)
            folder_id: Optional folder ID to list files from specific folder
            
        Returns:
            List of file dictionaries with id, name, mimeType, and other metadata
        """
        try:
            query = ""
            if folder_id:
                query = f"'{folder_id}' in parents and trashed=false"
            else:
                query = "trashed=false"
            
            results = self.service.files().list(
                pageSize=page_size,
                fields="nextPageToken, files(id, name, mimeType, size, createdTime, modifiedTime, parents, webViewLink)",
                q=query,
                orderBy="modifiedTime desc"
            ).execute()
            
            items = results.get('files', [])
            
            if not items:
                print('No files found.')
                return []
            
            print(f'Found {len(items)} files:')
            for item in items:
                size = item.get('size', 'N/A')
                if size != 'N/A':
                    size = self._format_file_size(int(size))
                
                print(f"- {item['name']} ({item['mimeType']}) - Size: {size}")
            
            return items
            
        except HttpError as error:
            print(f'An error occurred: {error}')
            return []
    
    def search_files(self, query: str, max_results: int = 50) -> List[Dict]:
        """
        Search for files in Google Drive
        
        Args:
            query: Search query (can be file name, content, etc.)
            max_results: Maximum number of results to return
            
        Returns:
            List of matching file dictionaries
        """
        try:
            # Construct search query
            search_query = f"name contains '{query}' and trashed=false"
            
            results = self.service.files().list(
                pageSize=max_results,
                fields="nextPageToken, files(id, name, mimeType, size, createdTime, modifiedTime, parents, webViewLink)",
                q=search_query,
                # orderBy="relevance desc"
            ).execute()
            
            items = results.get('files', [])
            
            if not items:
                print(f'No files found matching "{query}".')
                return []
            
            print(f'Found {len(items)} files matching "{query}":')
            for item in items:
                size = item.get('size', 'N/A')
                if size != 'N/A':
                    size = self._format_file_size(int(size))
                
                print(f"- {item['name']} ({item['mimeType']}) - Size: {size}")
            
            return items
            
        except HttpError as error:
            print(f'An error occurred: {error}')
            return []
    
    def search_files_advanced(self, 
                            name_contains: Optional[str] = None,
                            mime_type: Optional[str] = None,
                            folder_id: Optional[str] = None,
                            max_results: int = 50) -> List[Dict]:
        """
        Advanced search with multiple criteria
        
        Args:
            name_contains: Search in file names
            mime_type: Filter by MIME type (e.g., 'application/vnd.google-apps.spreadsheet')
            folder_id: Search within specific folder
            max_results: Maximum number of results
            
        Returns:
            List of matching file dictionaries
        """
        try:
            query_parts = ["trashed=false"]
            
            if name_contains:
                query_parts.append(f"name contains '{name_contains}'")
            
            if mime_type:
                query_parts.append(f"mimeType='{mime_type}'")
            
            if folder_id:
                query_parts.append(f"'{folder_id}' in parents")
            
            search_query = " and ".join(query_parts)
            
            results = self.service.files().list(
                pageSize=max_results,
                fields="nextPageToken, files(id, name, mimeType, size, createdTime, modifiedTime, parents, webViewLink)",
                q=search_query,
                orderBy="modifiedTime desc"
            ).execute()
            
            items = results.get('files', [])
            
            print(f'Advanced search found {len(items)} files:')
            for item in items:
                size = item.get('size', 'N/A')
                if size != 'N/A':
                    size = self._format_file_size(int(size))
                
                print(f"- {item['name']} ({item['mimeType']}) - Size: {size}")
            
            return items
            
        except HttpError as error:
            print(f'An error occurred: {error}')
            return []
    
    def get_file_info(self, file_id: str) -> Optional[Dict]:
        """
        Get detailed information about a specific file
        
        Args:
            file_id: Google Drive file ID
            
        Returns:
            File information dictionary or None if not found
        """
        try:
            file_info = self.service.files().get(
                fileId=file_id,
                fields="id, name, mimeType, size, createdTime, modifiedTime, parents, webViewLink, owners, permissions"
            ).execute()
            
            return file_info
            
        except HttpError as error:
            print(f'An error occurred: {error}')
            return None
    
    def _format_file_size(self, size_bytes: int) -> str:
        """Convert bytes to human readable format"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        import math
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        return f"{s} {size_names[i]}"

# Common MIME types for reference
MIME_TYPES = {
    'google_sheets': 'application/vnd.google-apps.spreadsheet',
    'google_docs': 'application/vnd.google-apps.document',
    'google_slides': 'application/vnd.google-apps.presentation',
    'pdf': 'application/pdf',
    'image': 'image/',
    'text': 'text/plain',
    'folder': 'application/vnd.google-apps.folder'
}

def main():
    """Example usage of the Google Drive API"""
    try:
        # print("init main")
        # Initialize the API (make sure you have credentials.json in the same directory)
        drive_api = GoogleDriveAPI()
        
        print("\n" + "="*50)
        print("LISTING FILES")
        print("="*50)
        
        # List recent files
        files = drive_api.list_files(page_size=10)
        
        print("\n" + "="*50)
        print("SEARCHING FILES")
        print("="*50)
        
        # Search for files containing "test" in the name
        search_results = drive_api.search_files("test", max_results=5)
        
        print("\n" + "="*50)
        print("ADVANCED SEARCH - Google Sheets only")
        print("="*50)
        
        # Search for Google Sheets only
        sheets = drive_api.search_files_advanced(
            mime_type=MIME_TYPES['google_sheets'],
            max_results=5
        )
        
        # If you have any files, get detailed info about the first one
        if files:
            print("\n" + "="*50)
            print("DETAILED FILE INFO")
            print("="*50)
            
            first_file = files[0]
            detailed_info = drive_api.get_file_info(first_file['id'])
            if detailed_info:
                print(f"File: {detailed_info['name']}")
                print(f"ID: {detailed_info['id']}")
                print(f"MIME Type: {detailed_info['mimeType']}")
                print(f"Created: {detailed_info.get('createdTime', 'N/A')}")
                print(f"Modified: {detailed_info.get('modifiedTime', 'N/A')}")
                print(f"Web View Link: {detailed_info.get('webViewLink', 'N/A')}")
    
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("\nMake sure you have:")
        print("1. Downloaded your OAuth2 credentials from Google Cloud Console")
        print("2. Saved them as 'credentials.json' in the same directory as this script")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == '__main__':
    main()