import os
import json
import base64
from openai import OpenAI
import cv2

class LLMService:
    def __init__(self):
        api_key = os.environ.get("NVIDIA_API_KEY")
        if not api_key:
            raise ValueError("NVIDIA_API_KEY environment variable not set.")
            
        self.client = OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=api_key
        )
        self.text_model = "nvidia/nemotron-3-ultra-550b-a55b"
        self.vision_model = "meta/llama-3.2-11b-vision-instruct"

    def _encode_image(self, image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def _extract_frame_from_video(self, video_path):
        try:
            vidcap = cv2.VideoCapture(video_path)
            success, image = vidcap.read()
            vidcap.release()
            if success:
                _, buffer = cv2.imencode('.jpg', image)
                return base64.b64encode(buffer).decode('utf-8')
        except Exception as e:
            print(f"Error extracting video frame: {e}")
        return None

    def generate_seo_content(self, local_path: str, is_video: bool = False) -> dict:
        """
        Generates SEO optimized title based on visual content.
        Returns a dictionary containing 'title'.
        """
        try:
            if is_video:
                base64_image = self._extract_frame_from_video(local_path)
                if not base64_image:
                    raise ValueError("Could not extract frame from video.")
            else:
                base64_image = self._encode_image(local_path)

            prompt = """
            You are an expert Social Media Manager and SEO Specialist.
            Analyze the attached image and create a simple, SEO-friendly title of EXACTLY 4 to 5 words based strictly on what is visible in the image.
            
            CRITICAL RULES:
            1. The title MUST be exactly 4 or 5 words long.
            2. Do NOT include any hashtags (#).
            3. Do NOT include any descriptions, captions, or extra text.
            4. End the title with EXACTLY ONE relevant emoji based on the subject.
            
            Provide the response strictly in the following JSON format:
            {
                "title": "Your 4-5 word title here 🚀"
            }
            
            Ensure the output is valid JSON and nothing else. Do not wrap in ```json blocks.
            """
            
            completion = self.client.chat.completions.create(
                model=self.vision_model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                temperature=0.7,
                max_tokens=512,
            )
            
            text = completion.choices[0].message.content
            
            # Clean up potential markdown formatting
            text = text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
                
            return json.loads(text.strip())
        except Exception as e:
            print(f"Error generating LLM content: {e}")
            # Fallback
            return {
                "title": "Amazing New Post ✨"
            }

    def select_best_image_for_variety(self, candidates, recent_categories):
        """Selects the best image from candidates to maximize variety based on recent categories."""
        if not candidates:
            return None
            
        if len(candidates) == 1:
            return candidates[0]

        filenames = [c['name'] for c in candidates]
        prompt = f"""
You are a content manager for a gaming/wildlife/sports page.
We want to post an image that provides maximum variety compared to what we recently posted.

Recently posted categories/themes:
{', '.join(recent_categories) if recent_categories else 'None'}

Here are the filenames of the candidates available:
{json.dumps(filenames, indent=2)}

Analyze the filenames. Pick the ONE filename that represents a theme, category, or style most different from the recently posted ones.
Reply ONLY with the exact filename from the list. Do not explain.
"""
        try:
            response = self.client.chat.completions.create(
                model=self.text_model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=100
            )
            selected_filename = response.choices[0].message.content.strip()
            
            # Find the candidate matching the filename
            for c in candidates:
                if c['name'] in selected_filename or selected_filename in c['name']:
                    return c
                    
            return candidates[0] # Fallback if LLM replies with weird text
        except Exception as e:
            return candidates[0] # Fallback
