import os
import requests

class DiscordService:
    def __init__(self):
        self.webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
        
        if not self.webhook_url:
            print("Warning: DISCORD_WEBHOOK_URL is not set. Reports will not be sent to Discord.")

    def send_report(self, report_data: dict):
        """
        Sends a formatted report to the Discord channel using an embed.
        """
        if not self.webhook_url:
            return
            
        status = report_data.get('status', 'Unknown')
        color = 3066993 if status == 'Success' else 15158332 # Green for Success, Red for Error
        
        # Build the embed fields
        fields = [
            {"name": "Status", "value": status, "inline": True},
            {"name": "Upload Time", "value": report_data.get('upload_time', 'N/A'), "inline": True},
            {"name": "Photo File Name", "value": report_data.get('file_name', 'N/A'), "inline": False}
        ]
        
        if status == 'Success':
            fields.extend([
                {"name": "Facebook Public Post URL", "value": f"[View Post]({report_data.get('public_url', '#')})", "inline": False},
                {"name": "Generated SEO Title", "value": report_data.get('title', 'N/A'), "inline": False},
                {"name": "Generated Caption", "value": report_data.get('caption', 'N/A'), "inline": False},
                {"name": "Generated Hashtags", "value": report_data.get('hashtags', 'N/A'), "inline": False}
            ])
        else:
            fields.append({
                "name": "Error Details", 
                "value": str(report_data.get('error', 'No error details provided.')), 
                "inline": False
            })
            
        # Add GitHub Actions Run URL if available
        github_run_id = os.environ.get('GITHUB_RUN_ID')
        github_repository = os.environ.get('GITHUB_REPOSITORY')
        if github_run_id and github_repository:
            run_url = f"https://github.com/{github_repository}/actions/runs/{github_run_id}"
            fields.append({"name": "GitHub Actions Run URL", "value": f"[View Logs]({run_url})", "inline": False})
            
        embed = {
            "title": "📸 Facebook Auto-Poster Report",
            "color": color,
            "fields": fields,
            "footer": {"text": "Automated Posting System"}
        }
        
        payload = {
            "embeds": [embed]
        }
        
        try:
            response = requests.post(self.webhook_url, json=payload)
            if response.status_code not in (200, 204):
                print(f"Failed to send Discord report: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"Exception while sending Discord report: {e}")
