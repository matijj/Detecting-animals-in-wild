import logging
import os
from datetime import datetime
import uuid
import cv2  # For handling video capture
from ultralytics import YOLO
from config import *

#1. Initialization and Setup Functions
def initialize_video_processing(source_path):
    """
    Initializes the video processing setup by loading the model, setting up file paths, and preparing the video capture.

    This function ensures the deep learning model is loaded, outputs are correctly routed to designated paths, and
    the video file is ready for frame-by-frame processing. It handles all preliminary steps necessary to start processing a video.

    Parameters:
    - source_path (str): The path to the video file to be processed.

    Returns:
    - tuple: A tuple containing the model, video capture object, video writer object, and paths for video output, detailed results, and summary.

    Raises:
    - RuntimeError: If the model fails to load, if the output paths cannot be set up, or if the video capture cannot be initialized.

    Each step of the initialization process is logged, providing detailed diagnostic information in case of failures.
    """

    try:
        model = YOLO('model/best.pt')
    except Exception as e:
        logging.error(f"Failed to load the model: {e}")
        raise RuntimeError(f"Model loading failed: {e}")

    try:
        # Setup file paths for outputs
        output_video_path, detailed_results_path, summary_path = setup_file_paths(source_path)
    except Exception as e:
        logging.error(f"Failed to setup file paths: {e}")
        raise RuntimeError(f"Error setting up file paths: {e}")

    try:
        # Initialize video capture
        cap = cv2.VideoCapture(source_path)
        if not cap.isOpened():
            raise IOError(f"Cannot open the video file {source_path}")

        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))

        return model, cap, out, output_video_path, detailed_results_path, summary_path
    except Exception as e:
        logging.error(f"Error during video capture initialization for {source_path}: {e}")
        # Clean up cap if it was opened
        if 'cap' in locals() and cap.isOpened():
            cap.release()
        raise RuntimeError(f"Failed to initialize video capture: {e}")


def setup_file_paths(source_path):
    """
    Generates unique file paths for the video output, detailed results, and summary based on the input source path.

    This function is critical for organizing the output files in a structured manner, using unique identifiers to avoid overwriting existing files.

    Parameters:
    - source_path (str): The path to the video file being processed.

    Returns:
    - tuple: A tuple containing paths for the video output, detailed results, and summary.

    The paths are generated using a timestamp and a unique UUID, ensuring that each processing session's outputs are stored separately.
    """

    unique_id = datetime.now().strftime("%Y%m%d%H%M%S") + "_" + str(uuid.uuid4())
    base_filename = os.path.splitext(os.path.basename(source_path))[0]
    output_video_path = f'{output_video_dir}/{base_filename}_{unique_id}.mp4'
    detailed_results_path = os.path.join(output_video_dir, f'{base_filename}_{unique_id}_detailed.txt')
    summary_path = os.path.join(output_video_dir, f'{base_filename}_{unique_id}_summary.txt')
    return output_video_path, detailed_results_path, summary_path



