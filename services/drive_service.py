import os
import io
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

class DriveService:
    def __init__(self):
        self.scopes = ['https://www.googleapis.com/auth/drive']
        self.creds = None
        
        # Load credentials from environment variable (JSON string) for GitHub Actions
        # Or fallback to a local credentials.json file
        creds_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")
        if creds_json:
            creds_dict = json.loads(creds_json)
            self.creds = service_account.Credentials.from_service_account_info(
                creds_dict, scopes=self.scopes
            )
        else:
            if os.path.exists("credentials.json"):
                self.creds = service_account.Credentials.from_service_account_file(
                    'credentials.json', scopes=self.scopes
                )
            else:
                raise Exception("Google Credentials not found. Set GOOGLE_CREDENTIALS_JSON env var or provide credentials.json")

        self.service = build('drive', 'v3', credentials=self.creds)

    def get_one_image(self, folder_id):
        """Fetches exactly one image from the specified Google Drive folder."""
        # Search for image files in the specific folder
        query = f"'{folder_id}' in parents and mimeType contains 'image/' and trashed=false"
        results = self.service.files().list(
            q=query,
            pageSize=1, # Get only one file
            fields="nextPageToken, files(id, name, mimeType)",
            orderBy="createdTime asc" # Oldest first, for example
        ).execute()
        
        items = results.get('files', [])
        if not items:
            return None
        return items[0]

    def download_image(self, file_id, file_name, download_path="downloads"):
        """Downloads the image to the local file system."""
        if not os.path.exists(download_path):
            os.makedirs(download_path)
            
        request = self.service.files().get_media(fileId=file_id)
        file_path = os.path.join(download_path, file_name)
        
        with io.FileIO(file_path, 'wb') as fh:
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
                
        return file_path

    def move_file(self, file_id, source_folder_id, destination_folder_id):
        """Moves the file to another folder so it won't be picked up again."""
        if not destination_folder_id:
            return False
            
        # Retrieve the existing parents to remove
        file = self.service.files().get(fileId=file_id, fields='parents').execute()
        previous_parents = ",".join(file.get('parents', []))
        
        # Move the file to the new folder
        self.service.files().update(
            fileId=file_id,
            addParents=destination_folder_id,
            removeParents=previous_parents,
            fields='id, parents'
        ).execute()
        return True
