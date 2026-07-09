# Facebook Auto-Poster (GitHub Actions)

This project automates posting images from a Google Drive folder to a Facebook Page, utilizing Google Gemini AI to generate SEO-optimized captions, titles, and hashtags based on the image's filename. It is designed to run automatically via GitHub Actions and sends a status report to a Discord channel.

## Features
- **Automated Execution:** Runs every hour via GitHub Actions.
- **Google Drive Integration:** Fetches one image at a time from a specific folder and optionally moves it to an "uploaded" folder after processing to prevent duplicate posts.
- **AI-Powered SEO Content:** Uses Google Gemini (gemini-1.5-flash) to read the image filename and generate highly engaging, Facebook-optimized captions and hashtags.
- **Human-like Delay:** Introduces a random delay (0 to 15 minutes) before uploading to Facebook to simulate organic human behavior.
- **Discord Reporting:** Sends a detailed embed report to a Discord channel with the upload status, public URL, generated content, and any errors.

## Setup Instructions

### 1. Google Drive API setup
1. Go to Google Cloud Console.
2. Enable **Google Drive API**.
3. Create a **Service Account** and generate a JSON Key.
4. Share the source Google Drive folder (and the destination folder, if using one) with the Service Account email address as an Editor.
5. Note down the Folder IDs (from the URL).

### 2. Facebook Graph API setup
1. Go to Facebook Developer Portal.
2. Create an App (Business type).
3. Generate a **Page Access Token** with permissions: `pages_manage_posts`, `pages_read_engagement`, `pages_show_list`.
4. Note down the **Page ID**.

### 3. Gemini API setup
1. Get an API key from Google AI Studio.

### 4. Discord setup
1. Go to your Discord server's channel settings.
2. Navigate to Integrations -> Webhooks.
3. Create a Webhook and copy the URL.

### 5. GitHub Repository Secrets
Add the following secrets to your GitHub repository (Settings > Secrets and variables > Actions):
- `GOOGLE_CREDENTIALS_JSON`: The entire JSON string from your Service Account key file.
- `GOOGLE_DRIVE_FOLDER_ID`: The ID of the folder containing images.
- `GOOGLE_DRIVE_UPLOADED_FOLDER_ID`: (Optional) The ID of the folder to move processed images to.
- `GEMINI_API_KEY`: Your Gemini API key.
- `FACEBOOK_PAGE_ACCESS_TOKEN`: Your Facebook Page Access Token.
- `FACEBOOK_PAGE_ID`: Your Facebook Page ID.
- `DISCORD_WEBHOOK_URL`: Your Discord Webhook URL.

## Running Locally
1. Clone the repository.
2. Create a virtual environment and run `pip install -r requirements.txt`.
3. Copy `.env.example` to `.env` and fill in the values (you can place `credentials.json` in the root folder instead of the JSON string for local testing).
4. Run `python main.py`.
