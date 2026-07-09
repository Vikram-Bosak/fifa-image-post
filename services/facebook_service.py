import os
import requests

class FacebookService:
    def __init__(self):
        self.access_token = os.environ.get("FACEBOOK_PAGE_ACCESS_TOKEN")
        self.page_id = os.environ.get("FACEBOOK_PAGE_ID")
        
        if not self.access_token or not self.page_id:
            raise ValueError("FACEBOOK_PAGE_ACCESS_TOKEN and FACEBOOK_PAGE_ID must be set in environment.")
            
        self.api_version = "v19.0" # Use a recent stable Graph API version
        self.base_url = f"https://graph.facebook.com/{self.api_version}/{self.page_id}/photos"
        
        # Automatically resolve Page Access Token if a User Token was provided
        self.access_token = self._get_page_access_token(self.access_token, self.page_id)

    def _get_page_access_token(self, user_token, page_id):
        """
        Queries /me/accounts to find the Page Access Token for the target Page ID.
        If not found or query fails, returns the user_token back as a fallback.
        """
        url = f"https://graph.facebook.com/{self.api_version}/me/accounts?limit=100&access_token={user_token}"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json().get('data', [])
                for page in data:
                    if str(page.get('id')) == str(page_id):
                        print(f"Successfully resolved Page Access Token for page: {page.get('name')} ({page_id})")
                        return page.get('access_token')
                print(f"Target Page ID {page_id} not found in user accounts. Falling back to provided token.")
            else:
                print(f"Failed to query /me/accounts (status {response.status_code}). Falling back to provided token.")
        except Exception as e:
            print(f"Error resolving Page Access Token: {e}. Falling back to provided token.")
        return user_token

    def _handle_api_error(self, response, step_name):
        if response.status_code >= 400:
            try:
                err_data = response.json()
                error_info = err_data.get('error', {})
                err_msg = error_info.get('message')
                err_code = error_info.get('code', 'unknown')
                err_subcode = error_info.get('error_subcode', 'unknown')
                if err_msg:
                    raise Exception(f"Facebook API Error ({step_name}): {err_msg} (code: {err_code}, subcode: {err_subcode})")
            except Exception as e:
                if "Facebook API Error" in str(e):
                    raise
            response.raise_for_status()

    def upload_reel(self, video_path: str, caption_text: str) -> dict:
        """
        Uploads a video to Facebook Reels using the multi-step Graph API process.
        """
        file_size = os.path.getsize(video_path)
        
        # Step 1: Initialize Upload
        init_url = f"https://graph.facebook.com/{self.api_version}/{self.page_id}/video_reels"
        init_payload = {
            'access_token': self.access_token,
            'upload_phase': 'start',
            'file_size': file_size
        }
        
        init_response = requests.post(init_url, data=init_payload)
        self._handle_api_error(init_response, "Initialize Upload")
        init_data = init_response.json()
        
        video_id = init_data.get('video_id')
        upload_url = init_data.get('upload_url')
        
        if not video_id or not upload_url:
            raise Exception("Failed to initialize Facebook upload session.")

        # Step 2: Upload Video Data
        headers = {
            'Authorization': f'OAuth {self.access_token}',
            'offset': '0',
            'file_size': str(file_size)
        }
        
        with open(video_path, 'rb') as f:
            video_data = f.read()
            
        upload_response = requests.post(upload_url, headers=headers, data=video_data)
        self._handle_api_error(upload_response, "Upload Video Data")
        
        # Step 3: Publish Video
        publish_url = f"https://graph.facebook.com/{self.api_version}/{self.page_id}/video_reels"
        publish_payload = {
            'access_token': self.access_token,
            'upload_phase': 'finish',
            'video_id': video_id,
            'video_state': 'PUBLISHED',
            'description': caption_text
        }
        
        publish_response = requests.post(publish_url, data=publish_payload)
        self._handle_api_error(publish_response, "Publish Video")
        publish_data = publish_response.json()
        
        if publish_data.get('success'):
            return {
                'id': video_id,
                'post_id': video_id,
                'public_url': f"https://www.facebook.com/{self.page_id}/videos/{video_id}"
            }
        else:
            raise Exception(f"Failed to publish reel: {publish_data}")

    def upload_photo(self, image_path: str, caption_text: str) -> dict:
        """
        Uploads a photo to the Facebook Page with the generated caption.
        Returns the response JSON which includes the 'id' and 'post_id'.
        """
        # Read the image file
        with open(image_path, 'rb') as img:
            files = {
                'source': img
            }
            data = {
                'message': caption_text,
                'access_token': self.access_token,
                'published': 'true'
            }
            
            response = requests.post(self.base_url, files=files, data=data)
            
            if response.status_code == 200:
                result = response.json()
                post_id = result.get('post_id') or result.get('id')
                
                public_url = ""
                if post_id:
                    if '_' in post_id:
                        parts = post_id.split('_')
                        public_url = f"https://www.facebook.com/{parts[0]}/posts/{parts[1]}"
                    else:
                        public_url = f"https://www.facebook.com/{self.page_id}/posts/{post_id}"
                
                result['public_url'] = public_url
                return result
            else:
                error_msg = f"Failed to upload to Facebook: {response.status_code} - {response.text}"
                raise Exception(error_msg)
