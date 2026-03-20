import cv2
import os

def convert_webp_to_mp4(input_path, output_path):
    print(f"Opening {input_path}...")
    cap = cv2.VideoCapture(input_path)
    
    if not cap.isOpened():
        print("Error: Could not open webp file.")
        return

    # Get properties
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps == 0 or fps > 60: # Handle weird webp FPS
        fps = 20.0
    
    print(f"Resolution: {width}x{height}, FPS: {fps}")

    # Define codec and create VideoWriter
    # 'mp4v' or 'avc1' are common for mp4
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        out.write(frame)
        frame_count += 1
    
    cap.release()
    out.release()
    print(f"Done! Processed {frame_count} frames. Saved to {output_path}")

if __name__ == "__main__":
    input_file = r"c:\Users\sg78b\OneDrive\Desktop\Programming code\Software Projects\IISc Hack\SkillForge-AI\docs\images\demo.webp"
    output_file = r"c:\Users\sg78b\OneDrive\Desktop\Programming code\Software Projects\IISc Hack\SkillForge-AI\docs\demo.mp4"
    convert_webp_to_mp4(input_file, output_file)
