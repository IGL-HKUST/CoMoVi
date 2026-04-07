import webdataset as wds
import os
import cv2
import sys

def extract_images(start_index, end_index, tar_url_template, output_dir):
    # Format start and end indices as six-digit strings
    start = f"{int(start_index):06d}"
    end = f"{int(end_index):06d}"
    
    # Construct the WebDataset URL with the range of tar files
    url = tar_url_template.format(start, end)
    
    # Ensure the output image directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Load the dataset, decode images, and rename extensions for compatibility
    dataset = (
        wds.WebDataset(url)
        .decode("rgb8")
        .rename(jpg="jpg;jpeg;png")
    )

    # Iterate over the dataset to save images
    for i, sample in enumerate(dataset):
        try:
            # Extract key and image data
            key = sample["__key__"]
            image_data = sample["jpg"]

            # Construct the full output path for the image
            base_dir = os.path.dirname(key)
            filename = os.path.basename(key) + ".jpg"
            image_path_dir = os.path.join(output_dir, base_dir)

            # Create the output directory if it doesn't exist
            os.makedirs(image_path_dir, exist_ok=True)
            
            image_path = os.path.join(image_path_dir, filename)

            # Save the image using OpenCV
            cv2.imwrite(image_path, cv2.cvtColor(image_data, cv2.COLOR_RGB2BGR))

        except Exception as e:
            print(f"Error processing sample {i}: {e}")
            continue

if __name__ == "__main__":
    # Parse command-line arguments for start and end indices
    start_index = sys.argv[1]
    end_index = sys.argv[2]

    # Define the URL template and output directory
    tar_url_template = "data/4DHumans/insta-train-vitpose-replicate/{0..{1}}.tar" #Download from 4D-Humans website
    output_dir = "data/training-images/insta"

    # Run the extraction function
    extract_images(start_index, end_index, tar_url_template, output_dir)
