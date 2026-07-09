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
                post_id = result.get('post_id')
                
                # Try to construct the public URL for the post
                # The post_id is typically in the format page_id_post_id
                public_url = ""
                if post_id:
                    parts = post_id.split('_')
                    if len(parts) == 2:
                        public_url = f"https://www.facebook.com/{parts[0]}/posts/{parts[1]}"
                    else:
                        public_url = f"https://www.facebook.com/{post_id}"
                
                result['public_url'] = public_url
                return result
            else:
                error_msg = f"Failed to upload to Facebook: {response.status_code} - {response.text}"
                raise Exception(error_msg)
