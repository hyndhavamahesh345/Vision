import os
import requests
import time

# The directory where your videos are located
VIDEO_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'videos'))

# The URL of the FastAPI endpoint for processing videos
UPLOAD_URL = "http://127.0.0.1:8001/api/upload"
STATUS_URL = "http://127.0.0.1:8001/api/status/{}"

def process_video(video_path):
    """Uploads a video for processing and monitors its status."""
    video_filename = os.path.basename(video_path)
    print(f"--- Processing: {video_filename} ---")

    with open(video_path, 'rb') as f:
        files = {'file': (video_filename, f, 'video/mp4')}
        try:
            # Upload the video
            upload_response = requests.post(UPLOAD_URL, files=files, timeout=30)
            upload_response.raise_for_status()
            job_id = upload_response.json().get("job_id")
            if not job_id:
                print(f"  [Error] Failed to get job_id for {video_filename}")
                return
            print(f"  [+] Video uploaded. Job ID: {job_id}")

            # Poll for job completion
            while True:
                status_response = requests.get(STATUS_URL.format(job_id), timeout=10)
                status_response.raise_for_status()
                job_status = status_response.json()

                if job_status["status"] == "completed":
                    print(f"  [Success] Job {job_id} completed.")
                    # print("  [Result]:", job_status.get("result"))
                    break
                elif job_status["status"] == "failed":
                    print(f"  [Error] Job {job_id} failed.")
                    print("  [Reason]:", job_status.get("error"))
                    break
                else:
                    print(f"  [*] Job status: {job_status['status']}...")
                    time.sleep(10)  # Wait for 10 seconds before checking again

        except requests.exceptions.RequestException as e:
            print(f"  [Error] An error occurred while processing {video_filename}: {e}")

def main():
    """Finds all video files and processes them."""
    if not os.path.isdir(VIDEO_DIR):
        print(f"Error: Video directory not found at {VIDEO_DIR}")
        return

    print(f"Searching for videos in: {VIDEO_DIR}")
    videos_to_process = [os.path.join(VIDEO_DIR, f) for f in os.listdir(VIDEO_DIR) if f.lower().endswith(('.mp4', '.mov', '.avi', '.mkv'))]

    if not videos_to_process:
        print("No video files found to process.")
        return

    print(f"Found {len(videos_to_process)} videos to process.")
    for video_path in videos_to_process:
        process_video(video_path)
    print("--- All videos processed. ---")

if __name__ == "__main__":
    main()
