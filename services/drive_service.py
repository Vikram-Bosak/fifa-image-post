import os
import io
import json
import random
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload

class DriveService:
    def __init__(self):
        self.scopes = ['https://www.googleapis.com/auth/drive']
        self.creds = None
        
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

    def get_random_images(self, folder_id, sample_size=10):
        """Fetches up to 50 images from the specified folder and returns a random sample."""
        query = f"'{folder_id}' in parents and (mimeType contains 'image/' or mimeType contains 'video/') and trashed=false"
        results = self.service.files().list(
            q=query,
            pageSize=50, # Fetch more to allow random selection
            fields="nextPageToken, files(id, name, mimeType)",
            orderBy="createdTime desc" # get relatively fresh ones
        ).execute()
        
        items = results.get('files', [])
        if not items:
            return []
            
        # Select random sample
        sample_size = min(sample_size, len(items))
        return random.sample(items, sample_size)

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
            
        try:
            file = self.service.files().get(fileId=file_id, fields='parents').execute()
            previous_parents = ",".join(file.get('parents', []))
            
            self.service.files().update(
                fileId=file_id,
                addParents=destination_folder_id,
                removeParents=previous_parents,
                fields='id, parents'
            ).execute()
            return True
        except Exception as e:
            print(f"Warning: Failed to move file to 'Uploaded' folder: {e}")
            return False

    def read_state(self, folder_id):
        """Reads the state.json file from the specified Drive folder."""
        query = f"'{folder_id}' in parents and name='state.json' and trashed=false"
        results = self.service.files().list(q=query, fields="files(id)").execute()
        items = results.get('files', [])
        
        if not items:
            return {"recent_categories": []}
            
        file_id = items[0]['id']
        request = self.service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
            
        return json.loads(fh.getvalue().decode('utf-8'))

    def write_state(self, folder_id, state_data):
        """Writes the state.json file to the specified Drive folder."""
        query = f"'{folder_id}' in parents and name='state.json' and trashed=false"
        results = self.service.files().list(q=query, fields="files(id)").execute()
        items = results.get('files', [])
        
        file_metadata = {'name': 'state.json', 'mimeType': 'application/json'}
        media = MediaIoBaseUpload(io.BytesIO(json.dumps(state_data).encode('utf-8')), mimetype='application/json', resumable=True)
        
        try:
            if not items:
                # Create new
                file_metadata['parents'] = [folder_id]
                self.service.files().create(body=file_metadata, media_body=media, fields='id').execute()
            else:
                # Update existing
                file_id = items[0]['id']
                self.service.files().update(fileId=file_id, media_body=media).execute()
        except Exception as e:
            print(f"Warning: Failed to write state.json (Service Account Quota issue?): {e}")

    def upload_file(self, local_path: str, folder_id: str, mime_type: str = 'text/plain') -> bool:
        """Uploads a local file to the specified Google Drive folder."""
        if not os.path.exists(local_path):
            print(f"Error: File {local_path} not found.")
            return False
            
        file_name = os.path.basename(local_path)
        file_metadata = {
            'name': file_name,
            'parents': [folder_id]
        }
        
        from googleapiclient.http import MediaFileUpload
        media = MediaFileUpload(local_path, mimetype=mime_type, resumable=True)
        
        try:
            print(f"Uploading {file_name} to Drive folder {folder_id}...")
            self.service.files().create(body=file_metadata, media_body=media, fields='id').execute()
            return True
        except Exception as e:
            print(f"Error uploading file to Drive: {e}")
            return False
