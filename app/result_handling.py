import os
import logging
from fastapi import HTTPException

import aiofiles

from app.zipping_json import * 
from app.reporting import *




#4. Result Handling and Preferences Management
def should_keep_file(file_info, user_preferences):
    """
    Determines whether a specific file should be retained based on user preferences.

    This function evaluates the type of file against the user's preferences to decide if it should be included in the final results. It supports filtering for original videos, annotated videos, detailed results, and summaries.

    Parameters:
    - file_info (dict): A dictionary containing details about the file, including its type (e.g., 'originalVideo', 'annotatedVideo').
    - user_preferences (set): A set of preferences from the user that may include options like 'keep_original', 'generate_annotated_video', etc.

    Returns:
    - bool: True if the file should be kept according to the user's preferences, False otherwise.

    The function helps in customizing the output of video processing operations by selectively retaining files based on the specified criteria, ensuring that only relevant files are made available for download or further use.
    """


    if file_info['type'] == 'originalVideo' and 'keep_original' in user_preferences:
        return True
    elif file_info['type'] == 'annotatedVideo' and 'generate_annotated_video' in user_preferences:
        return True
    elif file_info['type'] == 'detailedResults' and 'keep_detailed_results' in user_preferences:
        return True
    elif file_info['type'] == 'summary' and 'keep_summary' in user_preferences:
        return True
    return False

def modify_result_based_on_preferences(result, user_preferences):
    """
    Modifies the processing result based on user preferences, filtering files to keep according to specified criteria.

    This function tailors the output of the video processing to meet user-specified conditions, such as retaining certain types of result files.

    Parameters:
    - result (dict): The original processing result dictionary.
    - user_preferences (set): Preferences that specify which types of result files to retain.

    Returns:
    - dict: The modified result dictionary with files filtered according to user preferences.
    """


    modified_result = result.copy()
    filtered_files = [file for file in modified_result.get('files', []) if should_keep_file(file, user_preferences)]
    modified_result['files'] = filtered_files
    return modified_result




def handle_files_for_single(source_path, output_video_path, detailed_results_path, summary_path, user_preferences, animals_detected, all_detailed_results):

    """
    Manages the file handling for single video processing, including deletion, saving, and summarizing based on detection results and user preferences.

    This function determines what to do with various files based on the detection outcome (whether animals were detected or not) and user settings. It removes unnecessary files, saves necessary outputs, and compiles a summary.

    Parameters:
    - source_path (str): The original path of the video file.
    - output_video_path (str): The path where the annotated video is saved.
    - detailed_results_path (str): The path where detailed detection results are written.
    - summary_path (str): The path where the summary of the detection is saved.
    - user_preferences (set): Preferences that affect file handling such as retaining original videos, generating annotated videos, and saving detailed results.
    - animals_detected (bool): Indicates whether any animals were detected in the video.
    - all_detailed_results (list): A list of detailed detection results.

    Returns:
    - dict: A dictionary containing URLs to access the saved files, keyed by their type such as 'summaryUrl', 'videoUrl', 'detailedResultsUrl', etc.

    The function handles files based on detection outcomes and user preferences, ensuring that only necessary files are kept and appropriately managed.
    """
 

    paths = {}

    try:
        if not animals_detected:
            # Handle the case where no animals are detected
            if os.path.exists(output_video_path):
                os.remove(output_video_path)
            if "keep_original" not in user_preferences and os.path.exists(source_path):
                os.remove(source_path)
            with open(summary_path, 'w') as f:
                f.write("No animals detected.")
            paths["summaryUrl"] = f'/download/{os.path.basename(summary_path)}'
        else:
            # Handle the case where animals are detected
            if "keep_original" in user_preferences:
                paths["videoUrl"] = f'/download/{os.path.basename(source_path)}'
            if 'generate_annotated_video' in user_preferences:
                paths["annotatedVideoUrl"] = f'/download/{os.path.basename(output_video_path)}'
            if "keep_detailed_results" in user_preferences:
                with open(detailed_results_path, 'w') as f:
                    for line in all_detailed_results:
                        f.write(f"{line}\n")
                paths["detailedResultsUrl"] = f'/download/{os.path.basename(detailed_results_path)}'
            compile_and_save_summary(all_detailed_results, summary_path)
            paths["summaryUrl"] = f'/download/{os.path.basename(summary_path)}'

        return paths

    except IOError as e:
        # Handle potential I/O errors during file operations
        logging.error(f"IOError occurred while handling files: {e}")
        raise Exception(f"Failed to handle files due to I/O error: {e}")
    except Exception as e:
        # Handle any other exceptions that may occur
        logging.error(f"An error occurred while handling files: {e}")
        raise Exception(f"An unexpected error occurred: {e}")




def handle_files_for_multiple(source_path, output_video_path, detailed_results_path, summary_path, user_preferences, all_detailed_results):
    """
    Handles file operations for multiple video processing results, including saving summaries, detailed results, and annotated videos based on user preferences.

    This function organizes and saves output files for video processing sessions that handle multiple videos simultaneously or need multiple output types. It compiles summaries, saves detailed results, and manages annotated video files as specified by user preferences. Additionally, it can delete original video files if not required to be retained.

    Parameters:
    - source_path (str): Path to the source video file.
    - output_video_path (str): Path where the annotated video is saved.
    - detailed_results_path (str): Path where detailed results are saved.
    - summary_path (str): Path where the summary of the detection is saved.
    - user_preferences (set): User preferences that may include flags for saving detailed results, generating annotated videos, and retaining the original video.
    - all_detailed_results (list): A list of detailed detection results generated by the video processing.

    Returns:
    - list: A list of dictionaries, each containing the path, type, and detection status of the processed file. This list is used to inform users about the outcome of their processing request and provide links to download the outputs.

    The function checks user preferences to determine which outputs to generate and whether to keep or delete certain files, ensuring compliance with specified requirements. It logs actions taken for each file type for traceability.
    """


    file_metadata = []
    if all_detailed_results:
        compile_and_save_summary(all_detailed_results, summary_path)
        file_metadata.append({"path": summary_path, "type": "summary", "animals_detected": True})

        if "keep_detailed_results" in user_preferences:
            with open(detailed_results_path, 'w') as f:
                for line in all_detailed_results:
                    f.write(f"{line}\n")
            file_metadata.append({"path": detailed_results_path, "type": "detailedResults", "animals_detected": True})

        if 'generate_annotated_video' in user_preferences:
            file_metadata.append({"path": output_video_path, "type": "annotatedVideo", "animals_detected": True})
    else:
        with open(summary_path, 'w') as f:
            f.write("No animals detected.")
        file_metadata.append({"path": summary_path, "type": "summary", "animals_detected": False})

        # Only attempt to delete the video if it exists to prevent errors.
        if os.path.exists(output_video_path):
            os.remove(output_video_path)

        # Delete the original video only if the user preferences specify it and the file exists.
        if "keep_original" not in user_preferences and os.path.exists(source_path):
            os.remove(source_path)

    return file_metadata

