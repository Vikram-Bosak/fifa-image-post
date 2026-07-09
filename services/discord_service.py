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
        is_success = (status == 'Success')
        
        file_name = report_data.get('file_name', 'N/A')
        title = report_data.get('title', 'N/A')
        caption = report_data.get('caption', 'N/A')
        hashtags = report_data.get('hashtags', 'N/A')
        public_url = report_data.get('public_url', 'N/A')
        
        github_repository = os.environ.get('GITHUB_REPOSITORY', 'Vikram-Bosak/fifa-image-post')
        github_run_id = os.environ.get('GITHUB_RUN_ID', '')
        repo_url = f"https://github.com/{github_repository}"
        run_url = f"{repo_url}/actions/runs/{github_run_id}" if github_run_id else repo_url
        
        # Build the message content based on the template
        message_content = f"✅ Pipeline Run Completed\n\n"
        message_content += f"🎬 Image Name:\n{title}\n\n"
        
        message_content += f"📤 Facebook Upload Status: {status}\n\n"
        
        if is_success:
            message_content += f"🏷️ SEO Title:\n{title}\n\n"
            message_content += f"📝 Description:\n{caption}\n\n{hashtags}\n\n"
            message_content += f"Original File: {file_name}\n\n"
            message_content += f"🔗 Facebook Post URL:\n{public_url}\n\n"
        else:
            message_content += f"❌ Error Details:\n{report_data.get('error', 'Unknown Error')}\n\n"
            
        message_content += f"📦 GitHub Repository:\n{repo_url}\n\n"
        message_content += f"📄 Workflow Run:\n{run_url}"
        
        payload = {
            "content": message_content
        }
        
        try:
            response = requests.post(self.webhook_url, json=payload)
            if response.status_code not in (200, 204):
                print(f"Failed to send Discord report: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"Exception while sending Discord report: {e}")
