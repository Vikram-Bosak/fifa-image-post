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
