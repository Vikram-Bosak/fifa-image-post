import os
import json
import google.generativeai as genai

class LLMService:
    def __init__(self):
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set.")
        genai.configure(api_key=api_key)
        # Using gemini-1.5-flash for text generation tasks as it is fast and efficient
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    def generate_seo_content(self, filename: str) -> dict:
        """
        Generates SEO optimized content for Facebook based on the filename.
        Returns a dictionary containing 'title', 'caption', 'description', and 'hashtags'.
        """
        # Remove extension from filename to get the base subject
        base_name = os.path.splitext(filename)[0]
        # Replace underscores or hyphens with spaces for better context
        subject = base_name.replace("_", " ").replace("-", " ")

        prompt = f"""
        You are an expert Social Media Manager and SEO Specialist for Facebook.
        I am going to post a photo. The original file name of the photo is "{subject}".
        Based on this subject, please generate highly engaging, SEO-optimized content for a Facebook post.
        
        Provide the response strictly in the following JSON format:
        {{
            "title": "An engaging, click-worthy short title",
            "caption": "A compelling Facebook caption (2-3 sentences) with emojis, designed to encourage engagement and sharing",
            "description": "A slightly longer description providing context or a story related to the subject",
            "hashtags": "#hashtag1 #hashtag2 #hashtag3 (provide 5-8 relevant, trending hashtags)"
        }}
        
        Ensure the output is valid JSON and nothing else.
        """
        
        try:
            response = self.model.generate_content(prompt)
            text = response.text
            
            # Clean up potential markdown formatting (like ```json ... ```)
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
                
            return json.loads(text.strip())
        except Exception as e:
            print(f"Error generating LLM content: {e}")
            # Fallback content in case of error
            return {
                "title": subject.title(),
                "caption": f"Check out this amazing photo of {subject}! 📸✨",
                "description": f"Here is a beautiful picture related to {subject}. Let us know what you think in the comments!",
                "hashtags": f"#{subject.replace(' ', '')} #photography #trending"
            }
