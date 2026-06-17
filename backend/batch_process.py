import os
import time
import requests
import glob
import json

API_URL = "http://localhost:8001/api"
VIDEO_FOLDER = r"c:\Users\SOBHASREE SADU\OneDrive\Desktop\Video\videos"
OUTPUT_FILE = r"c:\Users\SOBHASREE SADU\OneDrive\Desktop\Video\batch_results.txt"

def process_videos():
    videos = glob.glob(os.path.join(VIDEO_FOLDER, "*.mp4"))
    if not videos:
        print(f"No videos found in {VIDEO_FOLDER}")
        return

    print(f"Found {len(videos)} videos. Submitting to API...")
    jobs = {}

    # Submit all videos
    for video_path in videos:
        filename = os.path.basename(video_path)
        with open(video_path, 'rb') as f:
            files = {'file': (filename, f, 'video/mp4')}
            try:
                response = requests.post(f"{API_URL}/upload", files=files)
                response.raise_for_status()
                data = response.json()
                jobs[filename] = data['job_id']
                print(f"Submitted {filename} -> Job ID: {data['job_id']}")
            except Exception as e:
                print(f"Failed to submit {filename}: {e}")

    print("\nWaiting for jobs to complete...")
    
    # Poll for completion
    completed_jobs = {}
    with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
        out.write("BATCH PROCESSING RESULTS\n")
        out.write("="*40 + "\n\n")

    while jobs:
        for filename, job_id in list(jobs.items()):
            try:
                res = requests.get(f"{API_URL}/status/{job_id}")
                status_data = res.json()
                status = status_data.get('status')
                
                if status == 'completed':
                    print(f"[{filename}] COMPLETED!")
                    # Get inventory
                    inv_res = requests.get(f"{API_URL}/inventory/{job_id}")
                    inventory = inv_res.json().get('inventory', [])
                    
                    with open(OUTPUT_FILE, "a", encoding="utf-8") as out:
                        out.write(f"VIDEO: {filename}\n")
                        out.write("-" * 20 + "\n")
                        for item in inventory:
                            out.write(f"- {item['name']}: {item['quantity']} (Room: {item['room']})\n")
                        out.write("\n")
                    
                    del jobs[filename]
                elif status == 'failed':
                    print(f"[{filename}] FAILED: {status_data.get('error')}")
                    del jobs[filename]
                else:
                    pipeline = status_data.get('pipeline', '')
                    print(f"[{filename}] Status: {status} - {pipeline}")
            except Exception as e:
                print(f"Error checking status for {filename}: {e}")
        
        if jobs:
            time.sleep(10)

    print(f"\nAll done! Results saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    process_videos()
