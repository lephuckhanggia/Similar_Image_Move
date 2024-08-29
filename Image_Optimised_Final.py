import os
from itertools import combinations
from PIL import Image
from concurrent.futures import ThreadPoolExecutor, as_completed
import numpy as np
import shutil
import torch
from timeit import default_timer as timer

device = "cuda" if torch.cuda.is_available() else "cpu"
print("Running by:", device)

# Directory to search for similar images
dirName = r"C:\AI Chalenge 2024\Keyframes_Optimized"
destination_path = r"C:\AI Chalenge 2024\Removed_Image"

# Function to list all image files in a directory and subdirectories
def list_of_files(dirName):
    all_files = []
    for entry in os.listdir(dirName):
        full_path = os.path.join(dirName, entry)
        if os.path.isdir(full_path):
            all_files.extend(list_of_files(full_path))
        elif entry.lower().endswith(('.jpg', '.jpeg', '.png')):
            all_files.append(full_path)
    return all_files

# Summarize an image into a 16x16 thumbnail
def summarise(img: Image.Image) -> np.ndarray:
    img_resized = img.resize((16, 16))
    img_array = np.array(img_resized)
    return img_array.mean(axis=2)  # Convert to grayscale by averaging RGB channels

# Calculate the difference between two images
def difference(sum1: np.ndarray, sum2: np.ndarray) -> float:
    return np.abs(sum1 - sum2).mean() / 255.0

# Function to move a file into a folder named after its original folder
def move_file_with_duplicate_folder(src_file, dest_path, diff_threshold=0.05):
    # Generate initial destination file path
    original_folder = os.path.basename(os.path.dirname(src_file))
    destination_folder = os.path.join(dest_path, original_folder)
    destination_file = os.path.join(destination_folder, os.path.basename(src_file))

    # Create the destination folder if it does not exist
    if not os.path.exists(destination_folder):
        os.makedirs(destination_folder)

    # If the file already exists, create a unique name
    if os.path.exists(destination_file):
        base, ext = os.path.splitext(destination_file)
        i = 1
        while os.path.exists(destination_file):
            destination_file = f"{base}_{i}{ext}"
            i += 1

    try:
        shutil.move(src_file, destination_file)
        print(f"Moved file: {src_file} to {destination_file}")
        return True
    except Exception as e:
        print(f"Error moving {src_file} to {destination_file}: {e}")
        return False

# Function to process and compare images
def process_and_compare(image_paths):
    summaries = {}
    with ThreadPoolExecutor() as executor:
        # Read and summarize all images
        futures = {executor.submit(summarise, Image.open(path)): path for path in image_paths}
        for future in as_completed(futures):
            path = futures[future]
            try:
                summary = future.result()
                summaries[path] = summary
            except Exception as e:
                print(f"Error processing {path}: {e}")

    # Compare images
    counter = 0
    for (path1, sum1), (path2, sum2) in combinations(summaries.items(), 2):
        diff = difference(sum1, sum2)
        print(f"Comparing {path1} and {path2}: Difference = {diff:.4f}")
        if diff < 0.05:
            if move_file_with_duplicate_folder(path2, destination_path):
                counter += 1
    print(f"Total files removed: {counter}")

# Main execution
start = timer()
if __name__ == "__main__":
    # List all image files in the directory and subdirectories
    all_image_files = list_of_files(dirName)
    
    # Ensure we have files to process
    if all_image_files:
        process_and_compare(all_image_files)
    else:
        print(f"No image files found in the directory: {dirName}")
print(f"Time to run: {timer()-start}")
