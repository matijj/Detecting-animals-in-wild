import logging
import asyncio
from fastapi import UploadFile, HTTPException
import numpy as np
import os
from pathlib import Path


from app.result_handling import  handle_files_for_multiple, handle_files_for_single, modify_result_based_on_preferences

from app.initialization import initialize_video_processing, setup_file_paths
from app.file_management import save_uploaded_file 
from config import * 

def process_video(source_path, user_preferences, is_multiple=False, every_n_frame=None):
    """
    Processes a single video file according to user-defined settings and preferences.

    Parameters:
    - source_path (str): Path to the source video file.
    - user_preferences (set): Set of preferences indicating which features to activate, such as generating annotated videos, getting_summary.
    - is_multiple (bool): Flag indicating whether the processing is part of a batch operation.
    - every_n_frame (int, optional): The number of frames to skip between processing. If None, a default setting is used.

    Raises:
    - HTTPException: If the video cannot be processed due to operational issues, including file access or processing errors.

    Returns:
    - dict: A dictionary containing processing status, messages, and paths to output files based on the execution results.

    This function initializes video processing, handles frame-by-frame analysis, and compiles results based on detection.
    It captures and logs key actions and outcomes at each stage for auditability and troubleshooting.
    """

    if every_n_frame is None:
        every_n_frame = get_every_n_frame()

    logging.info(f"Starting video processing for {source_path} with frame skip {every_n_frame}")
    try:
        model, cap, out, output_video_path, detailed_results_path, summary_path = initialize_video_processing(source_path)
        frame_counter = 0
        all_detailed_results = []

        while cap.isOpened():
            success, frame = cap.read()
            if not success:
                logging.debug(f"No more frames to read in {source_path}")
                break
            frame_counter += 1

            try:
                annotated_frame, detailed_results = process_and_track_frame(frame, model, frame_counter, every_n_frame)
                if 'generate_annotated_video' in user_preferences and out is not None:
                    out.write(annotated_frame)
                all_detailed_results.extend(detailed_results)
            except Exception as e:
                logging.error(f"Error processing frame {frame_counter} of video {source_path}: {e}")
                continue  # Depending on severity you might want to just log and continue

        cap.release()
        if out is not None:
            out.release()

        animals_detected = bool(all_detailed_results)
        result = {
            "status": "Animals detected" if animals_detected else "No animals detected",
            "message": "The uploaded video contains identifiable wildlife species." if animals_detected else "No animals detected in the uploaded video."
        }

        if is_multiple:
            file_metadata = handle_files_for_multiple(source_path, output_video_path, detailed_results_path, summary_path, user_preferences, all_detailed_results)
            result['files'] = file_metadata
        else:
            paths = handle_files_for_single(source_path, output_video_path, detailed_results_path, summary_path, user_preferences, animals_detected, all_detailed_results)
            result['paths'] = paths

        logging.info(f"Completed video processing for {source_path}")
        return result
    except Exception as e:
        logging.error(f"Failed to process video {source_path}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process video: {str(e)}")






#RADI ALI MENJAS ZBOG MLTIPLE U MAIN NEKAD VRACA DICTIONARY NEKAD SET

#def process_video(source_path, user_preferences, is_multiple=False, every_n_frame=None):
#    if every_n_frame is None:
#        every_n_frame = get_every_n_frame()
#
#    try:
#        model, cap, out, output_video_path, detailed_results_path, summary_path = initialize_video_processing(source_path)
#        frame_counter = 0
#        all_detailed_results = []
#
#        while cap.isOpened():
#            success, frame = cap.read()
#            if not success:
#                break
#            frame_counter += 1
#
#            try:
#                annotated_frame, detailed_results = process_and_track_frame(frame, model, frame_counter, every_n_frame)
#                if 'generate_annotated_video' in user_preferences and out is not None:
#                    out.write(annotated_frame)
#                all_detailed_results.extend(detailed_results)
#            except Exception as e:
#                logging.error(f"Error processing frame {frame_counter} of video {source_path}: {e}")
#                raise HTTPException(status_code=500, detail=f"Error processing frame {frame_counter}: {str(e)}")
#
#    except Exception as e:
#        logging.error(f"Failed to process video {source_path}: {e}")
#        raise HTTPException(status_code=500, detail=f"Failed to process video: {str(e)}")
#    finally:
#        cap.release()
#        if out is not None:
#            out.release()
#
#    animals_detected = bool(all_detailed_results)
#    result = {
#        "status": "Animals detected" if animals_detected else "No animals detected",
#        "message": "The uploaded video contains identifiable wildlife species." if animals_detected else "No animals detected in the uploaded video."
#    }
#
#    if is_multiple:
#        file_metadata = handle_files_for_multiple(source_path, output_video_path, detailed_results_path, summary_path, user_preferences, all_detailed_results)
#        result['files'] = file_metadata
#    else:
#        paths = handle_files_for_single(source_path, output_video_path, detailed_results_path, summary_path, user_preferences, animals_detected, all_detailed_results)
#        result['paths'] = paths
#
#    return result




#2. Video Processing Core Functions
def save_to_list(data):
    """
    Converts the given data into a list format if possible. This function is used to ensure compatibility and manageability of data types during video processing.

    This utility function attempts to convert numpy arrays to Python lists to facilitate easier handling and manipulation in processes that do not support numpy array directly. If the data is already a list or not convertible, it is returned as is.

    Parameters:
    - data (any): Data that needs to be converted to a list, typically a numpy array or any data type that supports the tolist() method.

    Returns:
    - list or original data: The data converted to a list if possible, or the original data if it does not support conversion.

    This function is critical in the video processing workflow where numpy arrays, common in image and video analysis, need to be converted for functions that require standard Python list structures.
    """

    try:
        return data.tolist()
    except AttributeError:
        return data

def process_and_track_frame(frame, model, frame_counter, every_n_frame):
    """
    Processes an individual frame using a specified model to detect and track features based on user-defined intervals.

    This function is invoked for each frame in the video processing loop but only processes frames based on the specified interval `every_n_frame`. It applies the model to detect features, which are then used to generate annotations and detailed results for that frame.

    Parameters:
    - frame (np.array): The current video frame to be processed.
    - model (Model): The detection model loaded to track objects in the frame.
    - frame_counter (int): The current frame number in the video processing sequence.
    - every_n_frame (int): The interval at which frames should be processed to detect features.

    Returns:
    - tuple: A tuple containing the annotated frame and a list of detailed results. The annotated frame includes visual markings of detected features, while the detailed results list includes text descriptions of these detections.

    Raises:
    - Exception: Logs and re-raises exceptions if the frame processing fails, providing details of the frame at which the error occurred.

    The function uses the model to detect objects in frames that meet the interval criteria, storing results and optionally updating the frame with annotations. This is part of a larger loop managed by `process_video`, allowing for conditional processing of every nth frame only.
    """


    detailed_results = []
    annotated_frame = frame
    #print("Starting frame processing:", frame_counter)

    if frame_counter % every_n_frame == 0:
        try:
            results = model.track(frame, persist=True, conf=0.75)
            #print("Results obtained:", results)

            if results and hasattr(results[0], 'boxes') and results[0].boxes is not None:
                cls = results[0].boxes.cls
                xywh = results[0].boxes.xywh
                ids = results[0].boxes.id
                #print("Box details - Class:", cls, "XYWH:", xywh, "IDs:", ids)

                if cls is not None and xywh is not None and ids is not None:
                    class_ids = cls.cpu().numpy()
                    boxes = xywh.cpu().numpy()
                    track_ids = ids.cpu().numpy()
                    #print("Processed numpy arrays - Class IDs:", class_ids, "Boxes:", boxes, "Track IDs:", track_ids)

                    for class_id, box, track_id in zip(class_ids, boxes, track_ids):
                        box_list = save_to_list(box)  # Using save_to_list to safely convert to list
                        animal_name = class_id_to_name.get(class_id, "Unknown")
                        detailed_results.append(f"Track ID: {track_id}, Animal: {animal_name}, Box: {box_list}")
                        #print("Appending detailed result:", detailed_results[-1])

                    annotated_frame = results[0].plot() if hasattr(results[0], 'plot') else frame
                    #print("Annotated Frame Updated:", annotated_frame)
        except Exception as e:
            logging.error(f"Failed to track frame {frame_counter}: {e}")
            #print("Error during tracking:", e)

    return annotated_frame, detailed_results



#RADI ALI TEST NE 
async def process_each_file(file, session_id, user_preferences, every_n_frame):
    """
    Asynchronously processes an individual video file within a session based on user preferences and specified frame intervals.

    This function is designed to handle the processing of each file uploaded in a batch operation. It saves the uploaded file, processes it, and modifies the result based on user preferences. This function is essential for parallel processing of multiple video files, improving throughput and efficiency in batch operations.

    Parameters:
    - file (UploadFile): The video file to be processed.
    - session_id (str): A unique identifier for the session under which this file is processed.
    - user_preferences (set): A set of preferences indicating which features to activate.
    - every_n_frame (int): The number of frames to skip between processing for efficiency.

    Returns:
    - dict: A dictionary containing the processed results, modified according to user preferences, or an error message if processing fails.

    Raises:
    - HTTPException: If the file cannot be saved or the video processing fails due to file-related issues.
    """

    save_path = None  # Initialize to avoid UnboundLocalError

    try:
        save_path = save_uploaded_file(file, session_id)

        result = process_video(save_path, user_preferences, is_multiple=True, every_n_frame=every_n_frame)

        modified_result = modify_result_based_on_preferences(result, user_preferences)
        return modified_result
    except Exception as e:
        logging.error(f"Error processing {file.filename} at {save_path}: {e}", exc_info=True)
        return {"error": f"Processing failed for {file.filename}: {str(e)}"}



