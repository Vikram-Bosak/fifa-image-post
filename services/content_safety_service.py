import os
import ffmpeg
import random

class ContentSafetyService:
    def __init__(self):
        # A list of words that could trigger spam or engagement-bait filters
        self.banned_words = [
            "share this", "share now", "tag a friend", "tag your", "like and share",
            "follow for more", "follow me", "click the link", "shocking", "you won't believe",
            "number 1", "secret", "hack", "giveaway", "free", "viral"
        ]
        
    def sanitize_text(self, text: str) -> str:
        """
        Removes or replaces engagement-bait and spam words from the text
        to ensure compliance with Facebook Community Standards.
        """
        if not text:
            return ""
            
        sanitized = text
        for word in self.banned_words:
            # Case insensitive replace
            # A simple replace works for basic functionality, in a real world scenario regex with word boundaries is better.
            import re
            sanitized = re.sub(r'\b' + re.escape(word) + r'\b', '', sanitized, flags=re.IGNORECASE)
            
        # Clean up double spaces left by removal
        sanitized = " ".join(sanitized.split())
        return sanitized

    def make_video_safe(self, input_path: str, output_path: str) -> bool:
        """
        Modifies a video using FFmpeg to avoid automated copyright claims.
        Techniques:
        1. Remove audio (most claims are music).
        2. Slight speed change (e.g. 1.05x).
        3. Minor crop to avoid exact pixel hashing.
        """
        try:
            # Check if file exists
            if not os.path.exists(input_path):
                print(f"Error: Video file {input_path} not found.")
                return False
                
            print(f"Applying safety modifications to {input_path}...")
            
            # Using ffmpeg-python to apply video filters
            # 1. setpts=0.95*PTS (speed up by ~5%)
            # 2. crop=iw*0.98:ih*0.98 (crop 2% from edges)
            
            stream = ffmpeg.input(input_path)
            
            # Apply video filters
            video = stream.video.filter('setpts', '0.95*PTS').filter('crop', 'iw*0.98', 'ih*0.98')
            
            # Output without audio (-an equivalent)
            out = ffmpeg.output(video, output_path, an=None, vcodec='libx264', crf=23, preset='fast')
            
            # Run ffmpeg (overwrite output if exists)
            ffmpeg.run(out, overwrite_output=True, quiet=True)
            
            print(f"Safe video generated at {output_path}")
            return True
        except Exception as e:
            print(f"Failed to modify video safely: {e}")
            return False
