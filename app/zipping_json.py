import csv
import glob
import io
import json
import logging
import os
import shutil
import threading
import time
import uuid
import zipfile
from collections import Counter, defaultdict
from datetime import datetime
from threading import Thread
from typing import List

import cv2
import pandas as pd
from ultralytics import YOLO

from config import *
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles





def save_manifest(output_dir: str, session_id: str, preferences: set, files: List[str]):
    """
    Saves a manifest file that contains the session preferences and paths to processed files.

    This function creates a JSON file that serves as a record for a processing session. It includes user preferences and the list of files processed during the session, aiding in tracking and reviewing the processing outcomes.

    Parameters:
    - output_dir (str): The directory where the manifest file will be saved.
    - session_id (str): The unique identifier for the session, used to name the manifest file.
    - preferences (set): The set of user-defined preferences that influenced the processing results.
    - files (List[str]): A list of file paths that were generated or used during the session.

    Returns:
    - None: This function does not return a value but raises exceptions on failures.

    Raises:
    - PermissionError: If the file cannot be written due to permission issues.
    - IOError: If there is an issue with file I/O operations, such as being unable to write to the directory.

    The manifest helps in providing a snapshot of the session's settings and outputs, which is essential for comprehensive documentation of the processing operations.
    """


    """Save session manifest with preferences and file paths."""
    manifest_path = os.path.join(output_dir, f"{session_id}_manifest.json")
    manifest_data = {
            "preferences": list(preferences),
            "files": files
            }
    try:
        with open(manifest_path, 'w') as manifest_file:
            json.dump(manifest_data, manifest_file)
    except PermissionError as e:
        logging.error(f"PermissionError when trying to write manifest file at {manifest_path}: {e}")
        raise PermissionError(f"Permission denied while saving the manifest: {e}")
    except IOError as e:
        logging.error(f"IOError when trying to write manifest file at {manifest_path}: {e}")
        raise IOError(f"An I/O error occurred while saving the manifest: {e}")









def create_zip_from_manifest(session_id, temp_predictions_dir):
    """
    Creates a ZIP file from the results and data specified in a session's manifest file.

    This function reads a manifest file associated with a given session ID, which details all the files to be included in the ZIP archive. It organizes files into categorized folders based on their detection status and includes overall summary files at the root of the ZIP. The function aims to provide a structured and comprehensive archive of session results for easy download and review.

    Parameters:
    - session_id (str): The unique identifier for the session whose files are to be archived.
    - temp_predictions_dir (str): The directory where the session's files and manifest are stored.

    Returns:
    - io.BytesIO: A BytesIO object containing the ZIP file data, ready for streaming or saving.

    Raises:
    - FileNotFoundError: If the manifest file does not exist, indicating no data to archive.
    - IOError: If there are issues reading the files or writing to the ZIP file.
    - Exception: For any other unexpected errors during the ZIP creation process.

    The function ensures all relevant files as per the manifest are safely packed into the ZIP, providing a structured output that reflects the organized data ready for review or further analysis.
    """

    zip_bytes_io = io.BytesIO()
    manifest_path = os.path.join(temp_predictions_dir, f"{session_id}_manifest.json")

    try:
        with open(manifest_path, 'r') as manifest_file:
            manifest_data = json.load(manifest_file)

        files_to_include = manifest_data.get('files', [])

        files_by_status = {'animals_detected': [], 'no_animals_detected': []}
        for file_info in files_to_include:
            if 'overall_summary.csv' not in file_info['path'] and 'overall_summary.xlsx' not in file_info['path']:
                status_key = 'animals_detected' if file_info.get("animals_detected") else 'no_animals_detected'
                files_by_status[status_key].append(file_info)


        with zipfile.ZipFile(zip_bytes_io, 'w', zipfile.ZIP_DEFLATED) as zipped:
            for summary_file in ["overall_summary.csv", "overall_summary.xlsx"]:
                summary_path = os.path.join(temp_predictions_dir, summary_file)
                if os.path.exists(summary_path):
                    zipped.write(summary_path, arcname=os.path.basename(summary_path))

            for status, files in files_by_status.items():
                if files:
                    for file_info in files:
                        file_basename = os.path.basename(file_info['path'])
                        # Example filename: 20240430154326_uuid_deer-night_otherinfo.mp4
                        parts = file_basename.split('_')
                        # Reorder filename to put descriptive part (like 'deer-night') first
                        if len(parts) > 2:
                            descriptive_part = parts[2]  # Adjust index based on your filename structure
                            other_parts = parts[:2] + parts[3:]
                            new_filename = f"{descriptive_part}_{'_'.join(other_parts)}"
                        else:
                            new_filename = file_basename  # Fallback to the original name if the expected format isn't met

                        arcname = os.path.join(status, new_filename)
                        file_path = os.path.join(temp_predictions_dir, file_info['path'])

                        if os.path.exists(file_path):
                            zipped.write(file_path, arcname=arcname)

        zip_bytes_io.seek(0)
        return zip_bytes_io

    except FileNotFoundError:
        logging.error(f"Manifest file not found for session {session_id}.")
        raise
    except IOError as e:
        logging.error(f"File I/O error occurred while creating ZIP for session {session_id}: {e}")
        raise
    except Exception as e:
        logging.error(f"An unexpected error occurred while creating the ZIP file for session {session_id}: {e}")
        raise




#        with zipfile.ZipFile(zip_bytes_io, 'w', zipfile.ZIP_DEFLATED) as zipped:
#            for summary_file in ["overall_summary.csv", "overall_summary.xlsx"]:
#                summary_path = os.path.join(temp_predictions_dir, summary_file)
#                if os.path.exists(summary_path):
#                    zipped.write(summary_path, arcname=os.path.basename(summary_path))
#
#            for status, files in files_by_status.items():
#                if files:
#                    for file_info in files:
#                        path_parts = file_info['path'].split('_')
#                        video_folder_name = path_parts[2] if len(path_parts) >= 3 else "misc"
#                        video_folder = os.path.join(status, video_folder_name)
#                        arcname = os.path.join(video_folder, os.path.basename(file_info['path']))
#                        file_path = os.path.join(temp_predictions_dir, file_info['path'])
#
#                        if os.path.exists(file_path):
#                            zipped.write(file_path, arcname=arcname)
#
#        zip_bytes_io.seek(0)
#        return zip_bytes_io
#
#    except FileNotFoundError:
#        logging.error(f"Manifest file not found for session {session_id}.")
#        raise
#    except IOError as e:
#        logging.error(f"File I/O error occurred while creating ZIP for session {session_id}: {e}")
#        raise
#    except Exception as e:
#        logging.error(f"An unexpected error occurred while creating the ZIP file for session {session_id}: {e}")
#        raise
#
