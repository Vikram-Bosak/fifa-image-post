import os
import time
import random
from datetime import datetime
from dotenv import load_dotenv

from services.drive_service import DriveService
from services.llm_service import LLMService
from services.facebook_service import FacebookService
from services.discord_service import DiscordService
from services.content_safety_service import ContentSafetyService

def main():
    # Load environment variables for local testing
    load_dotenv()
    
    discord_service = DiscordService()
    report_data = {
        'status': 'Failed',
        'upload_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'file_name': 'N/A',
        'public_url': 'N/A',
        'title': 'N/A',
        'caption': 'N/A',
        'hashtags': 'N/A',
        'error': None
    }
    
    try:
        print("Initializing services...")
        drive_service = DriveService()
        llm_service = LLMService()
        facebook_service = FacebookService()
        safety_service = ContentSafetyService()
        
        source_folder_id = os.environ.get("GOOGLE_DRIVE_FOLDER_ID")
        uploaded_folder_id = os.environ.get("GOOGLE_DRIVE_UPLOADED_FOLDER_ID")
        
        if not source_folder_id:
            raise ValueError("GOOGLE_DRIVE_FOLDER_ID is not set.")
            
        print("Fetching an image from Google Drive...")
        # 1. Fetch random candidates from Drive
        candidates = drive_service.get_random_images(source_folder_id, sample_size=10)
        if not candidates:
            print("No images found in the specified Drive folder.")
            report_data['status'] = 'Skipped'
            report_data['error'] = 'No new images found in Google Drive.'
            discord_service.send_report(report_data)
            return
            
        print(f"Found {len(candidates)} candidate images.")
        
        # 2. Read State to enforce variety
        state_data = drive_service.read_state(source_folder_id)
        recent_categories = state_data.get('recent_categories', [])
        
        # 3. Select best image for variety using LLM
        selected_image = llm_service.select_best_image_for_variety(candidates, recent_categories)
        file_id = selected_image['id']
        file_name = selected_image['name']
        report_data['file_name'] = file_name
        
        print(f"Selected Image for Variety: {file_name}")

        # 4. Generate content
        print("Generating SEO content using LLM...")
        seo_data = llm_service.generate_seo_content(file_name)
        
        title = seo_data.get('title', '')
        caption = seo_data.get('caption', '')
        description = seo_data.get('description', '')
        hashtags = seo_data.get('hashtags', '')
        
        report_data['title'] = title
        report_data['caption'] = caption
        report_data['hashtags'] = hashtags
        
        final_caption = f"{title}\n\n{caption}\n\n{description}\n\n{hashtags}"
        
        # Sanitize final caption using the safety service
        final_caption = safety_service.sanitize_text(final_caption)
        
        # 5. Download the media
        print("Downloading media...")
        local_path = drive_service.download_image(file_id, file_name)
        
        is_video = file_name.lower().endswith(('.mp4', '.mov', '.avi', '.mkv'))
        
        # 6. Safety Checks and Modification
        safe_local_path = local_path.replace('.', '_safe.')
        if is_video:
            success = safety_service.make_video_safe(local_path, safe_local_path)
        else:
            success = safety_service.make_image_safe(local_path, safe_local_path)
            
        if success:
            # Replace the original local path with the safe one
            if os.path.exists(local_path):
                os.remove(local_path)
            local_path = safe_local_path
        else:
            print("Warning: Could not make media safe. Proceeding with original... (High Risk)")

        # Human-like random delay (Only if PRODUCTION_MODE is true)
        is_production = os.environ.get("PRODUCTION_MODE", "false").lower() == "true"
        
        if is_production:
            delay_minutes = random.uniform(0, 15)
            delay_seconds = int(delay_minutes * 60)
            print(f"Production Mode ON: Simulating human delay... waiting for {delay_seconds} seconds ({delay_minutes:.2f} minutes).")
            time.sleep(delay_seconds)
        else:
            print("Production Mode OFF: Skipping random delay for testing.")
        
        print("Uploading to Facebook...")
        # Update upload time after sleep
        report_data['upload_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if is_video:
            fb_result = facebook_service.upload_reel(local_path, final_caption)
            print(f"Successfully uploaded video to Facebook Reels! Video ID: {fb_result.get('id')}")
        else:
            fb_result = facebook_service.upload_photo(local_path, final_caption)
            print(f"Successfully uploaded photo to Facebook! Post ID: {fb_result.get('post_id')}")
        
        report_data['public_url'] = fb_result.get('public_url', 'URL not found')
        
        # Move file in Drive so it doesn't get picked up again
        if uploaded_folder_id:
            print("Moving processed file to 'Uploaded' folder in Google Drive...")
            drive_service.move_file(file_id, source_folder_id, uploaded_folder_id)
            
        # Update state with new category (using filename as proxy for category)
        recent_categories.insert(0, file_name.split('.')[0])
        state_data['recent_categories'] = recent_categories[:5] # keep last 5
        drive_service.write_state(source_folder_id, state_data)
        print("Updated state.json with recent categories.")
            
        # Clean up local file
        if os.path.exists(local_path):
            os.remove(local_path)
            
        report_data['status'] = 'Success'
        print("Workflow completed successfully.")
        
    except Exception as e:
        error_msg = str(e)
        print(f"An error occurred: {error_msg}")
        report_data['status'] = 'Error'
        report_data['error'] = error_msg
        
        # Action Taken for failed upload
        if report_data.get('file_name') != 'N/A' and 'file_id' in locals() and 'local_path' in locals() and 'source_folder_id' in locals():
            print("Handling failed upload...")
            
            # Try to get folder from env, else create/get 'Failed Uploads' inside source folder
            failed_folder_id = os.environ.get("GOOGLE_DRIVE_FAILED_FOLDER_ID")
            if not failed_folder_id:
                failed_folder_id = drive_service.get_or_create_folder("Failed Uploads", source_folder_id)
                
            if failed_folder_id:
                try:
                    # 1. Create .txt file with metadata
                    base_name = os.path.splitext(report_data['file_name'])[0]
                    txt_filename = f"{base_name}.txt"
                    txt_path = os.path.join(os.path.dirname(local_path), txt_filename)
                
                    with open(txt_path, 'w', encoding='utf-8') as f:
                        f.write(f"Title: {report_data.get('title')}\n")
                        f.write(f"Caption: {report_data.get('caption')}\n")
                        f.write(f"Hashtags: {report_data.get('hashtags')}\n")
                        f.write(f"Upload Time: {report_data.get('upload_time')}\n")
                        f.write(f"Facebook Page Name: {os.environ.get('FACEBOOK_PAGE_ID')}\n")
                        f.write(f"Error Message: {error_msg}\n")
                    
                    # 2. Upload .txt to Failed Folder
                    drive_service.upload_file(txt_path, failed_folder_id, mime_type='text/plain')
                    
                    # 3. Move original image to Failed Folder
                    drive_service.move_file(file_id, source_folder_id, failed_folder_id)
                    
                    report_data['failed_action_taken'] = f"Image and Metadata ({txt_filename}) successfully moved to the 'Failed Uploads' folder."
                    print(report_data['failed_action_taken'])
                    
                    # Cleanup .txt locally
                    if os.path.exists(txt_path):
                        os.remove(txt_path)
                except Exception as cleanup_error:
                    report_data['failed_action_taken'] = f"Attempted to move failed file, but encountered error: {cleanup_error}"
                    print(report_data['failed_action_taken'])
        
    finally:
        # Always send the report at the end
        print("Sending Discord report...")
        discord_service.send_report(report_data)

if __name__ == "__main__":
    main()
