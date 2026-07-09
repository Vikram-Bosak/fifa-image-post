import os
import json
from openai import OpenAI

class LLMService:
    def __init__(self):
        api_key = os.environ.get("NVIDIA_API_KEY")
        if not api_key:
            raise ValueError("NVIDIA_API_KEY environment variable not set.")
            
        self.client = OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=api_key
        )
        self.model = "nvidia/nemotron-3-ultra-550b-a55b"

    def generate_seo_content(self, filename: str) -> dict:
        """
        Generates SEO optimized content for Facebook based on the filename.
        Returns a dictionary containing 'title', 'caption', 'description', and 'hashtags'.
        """
        base_name = os.path.splitext(filename)[0]
        subject = base_name.replace("_", " ").replace("-", " ")

        prompt = f"""
        You are an expert Social Media Manager and SEO Specialist for Facebook.
        I am going to post a photo. The original file name of the photo is "{subject}".
        Based strictly on this subject, please generate highly engaging, SEO-optimized content for a Facebook post.
        
        CRITICAL RULES:
        1. The generated title, caption, description, and hashtags MUST be entirely relevant to the subject: "{subject}".
        2. Do NOT use any unrelated keywords or hashtags.
        3. Keep the context accurate and aligned with what the filename suggests.
        4. ANTI-SPAM POLICY: NEVER use clickbait or engagement-bait phrases (e.g., "Share this", "Tag a friend", "Click here", "Shocking", "Viral").
        5. The content MUST be completely safe, Policy-compliant, and avoid any misleading statements.
        
        Provide the response strictly in the following JSON format:
        {{
            "title": "An engaging, click-worthy short title about {subject}",
            "caption": "A compelling Facebook caption (2-3 sentences) with emojis, strictly related to {subject}",
            "description": "A slightly longer description providing context or a story related to {subject}",
            "hashtags": "#hashtag1 #hashtag2 #hashtag3 (provide 5-8 strictly relevant, trending hashtags)"
        }}
        
        Ensure the output is valid JSON and nothing else. Do not wrap in ```json blocks.
        """
        
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=1,
                top_p=0.95,
                max_tokens=2048,
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
            # Dynamic Fallback content based on subject
            return {
                "title": f"Amazing {subject.title()}",
                "caption": f"Check out this incredible view of {subject}! What are your thoughts? Let us know below! ✨👇\n\n#{subject.replace(' ', '')}",
                "hashtags": f"#{subject.replace(' ', '')} #trending #viral"
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
                model=self.model,
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
