import asyncio
from fastapi import FastAPI, Query

from typing import Dict
import io
import json
import logging
import os
import shutil
import uuid
import warnings
import zipfile
from datetime import datetime

import cv2
import pandas as pd
from collections import Counter, defaultdict
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from ultralytics import YOLO
from ultralytics.utils.autobatch import autobatch

import glob


# Custom module imports
from config import *
from app.zipping_json import *
from app.video_processing import process_video, process_and_track_frame, process_each_file
from app.file_management import *
from app.initialization import *
from app.reporting import *

#for docs examples
from fastapi import FastAPI, HTTPException, Form, File, UploadFile, Path
from pydantic import BaseModel, Field
from typing import Optional


# Configure warnings and logging
warnings.filterwarnings("ignore", category=DeprecationWarning)
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

from pydantic import BaseModel, Field



 

# Initialize FastAPI app
app = FastAPI()


temp_predictions_dir = 'temp_predictions_file'
os.makedirs(temp_predictions_dir, exist_ok=True)



# Mount static directories to serve static files and downloads
app.mount("/download", StaticFiles(directory=temp_predictions_dir), name="download")
app.mount("/static", StaticFiles(directory=static_files_dir), name="static")

# Set up Jinja2 templates for HTML responses
templates = Jinja2Templates(directory=templates_dir)

@app.get("/", response_class=HTMLResponse)
async def upload_form(request: Request):
    """
    Serve the main page to the client using Jinja2 templates.

    This endpoint handles the root URL and uses Jinja2 templating engine to render the `index.html`. 
    It passes the request context to the template, enabling dynamic content rendering based on the request.

    Parameters:
    - request (Request): The request object that includes details about the HTTP request.

    Returns:
    - TemplateResponse: Renders the 'index.html' with the given context.

    Example endpoint usage:
    - GET /

    This function is typically called when the user accesses the root URL of the application.
    """
    return templates.TemplateResponse("index.html", {"request": request})



@app.post("/upload_and_track/")
async def upload_and_track(
    file: UploadFile = File(..., description="Upload video file in MP4 or AVI format."),
    preference: str = Form(..., description="keep_summary, generate_annotated_video, keep_detailed_results"),
    every_n_frame: int = Form(3, description="Process every Nth frame for features.")
):
    """
    Processes an uploaded video file according to specified frame intervals and generates downloadable results.

    This endpoint is designed for a single video file upload where the user specifies how often frames should be processed.
    It ensures the file is in a supported format, processes it, and provides links to download the annotated video, detailed results,
    and a summary of the detections. This operation is user-initiated through an interface where they upload a video and set frame processing preferences.


    Parameters:
    - file (UploadFile): The video file uploaded by the user. Must be in MP4 or AVI format.
    - every_n_frame (int): Specifies the frequency of frames to process (e.g., every 3 frames).

    Raises:
    - HTTPException: 400 error if the file format is unsupported; 500 errors for failures in file saving or processing.

    Returns:
    - JSONResponse: Contains links to download the annotated video, detailed results, and summary, reflecting the outcomes of the processing.

    """

    supported_formats = {'.mp4', '.avi'}
    if not file.filename.lower().endswith(tuple(supported_formats)):
        logging.warning(f"Attempted upload with unsupported file format: {file.filename}")
        raise HTTPException(status_code=400, detail="Invalid file type.")

    cleanup_directory(temp_predictions_dir)
    save_path = os.path.join(temp_predictions_dir, f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4()}_{file.filename}")
    logging.info(f"Attempting to save uploaded file to {save_path}")

    try:
        with open(save_path, 'wb') as buffer:
            shutil.copyfileobj(file.file, buffer)
        logging.info(f"File saved successfully: {save_path}")
    except IOError as e:
        logging.error(f"Failed to save {file.filename}: {e}")
        raise HTTPException(status_code=500, detail="Failed to save file.")

    try:
        user_preferences = {pref.strip() for pref in preference.split(",")}
        logging.debug(f"User preferences parsed: {user_preferences}")
        result = process_video(save_path, user_preferences, is_multiple=False, every_n_frame=every_n_frame)
        logging.debug(f"Video processed successfully for {file.filename}")


        response_content = {
            "status": result["status"],
            "message": result["message"],
            "paths": {key: value for key, value in result.get("paths", {}).items() if value}
        }
        return JSONResponse(content=response_content, status_code=200)

    except Exception as e:
        logging.error(f"Processing error for {file.filename}: {e}")
        raise HTTPException(status_code=500, detail="Video processing failed.")




@app.post("/upload_and_track_multiple/")
async def upload_and_track_multiple(
    files: List[UploadFile] = File(..., description="Upload video files in MP4 or AVI format."),
    preference: str = Form(..., description="keep_summary, generate_annotated_video, keep_detailed_results"),
    every_n_frame: int = Form(3, description="Process every Nth frame for features.")
):

    """
    Receives multiple video files and processes each according to the specified user preferences and frame intervals.
    This endpoint is designed to handle batch uploads of video files for processing, where each file can be independently processed
    based on provided preferences such as generating annotated videos, keeping detailed results, and creating summaries.

    Preferences: keep_summary, generate_annotated_video, keep_detailed_results

    Parameters:
    - files (List[UploadFile]): A list of video files uploaded by the user. Must be in MP4 or AVI format.
    - preference (str): Comma-separated string of preferences affecting processing. These preferences determine whether to generate
      annotated videos, save detailed results, and create summaries.
    - every_n_frame (int): The interval at which frames are processed to detect features or activities in the video.

    Raises:
    - HTTPException: Returns a 400 error if no files are provided or if an unsupported file format is detected.
      Returns a 500 error if there is an error during file processing.

    Returns:
    - JSONResponse: The response includes the session ID, paths to the processed files (organized based on detection results),
      and a summary in CSV and Excel format. Errors are also returned in the response if any occur during processing.

    The function utilizes asynchronous processing to handle multiple files concurrently, optimizing performance and scalability.
    It logs significant actions such as file saving, video processing start and end, and any errors or exceptions encountered.
    """

    cleanup_directory(temp_predictions_dir)
    logging.debug(f"Directory cleaned: {temp_predictions_dir}")

    if not files:
        logging.error("No files were provided.")
        return JSONResponse(status_code=400, content={"error": "No files provided"})

    valid_formats = {'.mp4', '.avi'}
    if not all(file.filename.lower().endswith(tuple(valid_formats)) for file in files):
        logging.error("Invalid file type detected among uploaded files.")
        return JSONResponse(status_code=400, content={"error": "Invalid file type, only MP4 and AVI files are allowed"})

    user_preferences = set(pref.strip() for pref in preference.split(","))
    session_id = datetime.now().strftime("%Y%m%d%H%M%S") + "_" + str(uuid.uuid4())
    logging.info(f"Session started: {session_id} with preferences {user_preferences}")

    try:
        tasks = [process_each_file(file, session_id, user_preferences, every_n_frame) for file in files]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        processed_files = []
        errors = []

        for result in results:
            if isinstance(result, Exception):
                error_detail = str(result)
                logging.error(f"Processing failed: {error_detail}")
                errors.append(error_detail)
            else:
                for file_info in result.get('files', []):
                    if not any(f['path'] == file_info['path'] for f in processed_files):
                        processed_files.append({
                            "path": os.path.relpath(file_info['path'], start=temp_predictions_dir),
                            "type": file_info['type'],
                            "animals_detected": file_info.get('animals_detected', 'Not detected')
                        })
        logging.debug(f"Files processed: {processed_files}")

        if errors:
            logging.error(f"Errors occurred during processing: {errors}")
            return JSONResponse(status_code=500, content={"session_id": session_id, "errors": errors})

        csv_path, excel_path = compile_overall_summary(temp_predictions_dir)
        processed_files.extend([
            {"path": os.path.relpath(csv_path, start=temp_predictions_dir), "type": "summaryCSV"},
            {"path": os.path.relpath(excel_path, start=temp_predictions_dir), "type": "summaryExcel"}
        ])
        logging.info("Summary files generated and added to the response.")

        save_manifest(temp_predictions_dir, session_id, user_preferences, processed_files)
        logging.info(f"Manifest saved for session {session_id}")

        response_content = {
            "session_id": session_id,
            "files_processed": len(processed_files),
            "errors": errors
        }
        return JSONResponse(status_code=200, content=response_content)
    except Exception as e:
        logging.critical(f"An unexpected error occurred during the request: {str(e)}", exc_info=True)
        return JSONResponse(status_code=500, content={"session_id": session_id, "error": f"Internal server error: {str(e)}"})


@app.get("/zip/download/{session_id}", responses={
    200: {
        "description": "ZIP file successfully created and ready for download.",
        "content": {
            "application/x-zip-compressed": {
                "example": "Binary data representing the ZIP file"
            }
        }
    },
    404: {
        "description": "No data available to download or session ID not found.",
        "content": {
            "application/json": {
                "example": {
                    "error": "No data available to download or session ID not found."
                }
            }
        }
    },
    422: {
        "description": "Validation error with detailed information.",
        "content": {
            "application/json": {
                "example": {
                    "detail": [
                        {
                            "loc": ["query", "session_id"],
                            "msg": "Session ID is required",
                            "type": "value_error.missing"
                        }
                    ]
                }
            }
        }
    },
    500: {
        "description": "Internal server error during the ZIP file creation process.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Failed to read or write ZIP file or unexpected error occurred."
                }
            }
        }
    }
})
async def zip_download(session_id: str = Path(..., description="Session ID obtained from the multi-upload endpoint")):
    """
    Generates a downloadable ZIP file containing the results of a processing session identified by the session_id.
    The ZIP file is created based on the manifest that details all the files associated with the given session.
    
    This endpoint checks if the session's results are compiled into a manifest and attempts to create a ZIP archive
    of these results. If successful, it provides a download link to the user; otherwise, it returns an error message.

    Parameters:
    - session_id (str): The unique identifier for the processing session whose results need to be zipped and downloaded.

    Raises:
    - HTTPException: Returns a 404 error if the manifest file for the session cannot be found or the ZIP file is empty,
      indicating that no data is available to download. It also returns a 500 error if there's a problem reading or writing
      the ZIP file or if an unexpected error occurs during the creation of the ZIP file.

    Returns:
    - StreamingResponse: A response that streams the ZIP file directly to the user's browser, prompting a file download.
      The Content-Disposition header suggests a filename for the ZIP file based on the session ID.

    The function logs the creation of the ZIP file, including its size, and any errors that occur during this process.
    This aids in debugging and ensures transparency in file handling operations.
    """
    try:
        zip_bytes_io = create_zip_from_manifest(session_id, temp_predictions_dir)
        logging.debug(f"ZIP file created with size: {zip_bytes_io.getbuffer().nbytes} bytes")

        if zip_bytes_io.getbuffer().nbytes == 0:
            logging.warning(f"ZIP file is empty for session {session_id}")
            return JSONResponse(content={"error": "No data available to download."}, status_code=404)
        response_headers = {
            "Content-Disposition": f"attachment; filename={session_id}_output.zip"
        }
        return StreamingResponse(iter([zip_bytes_io.read()]), media_type="application/x-zip-compressed", headers=response_headers)

    except FileNotFoundError:
        logging.error(f"Manifest file not found for session {session_id}")
        return JSONResponse(content={"error": "Manifest file not found. Invalid session ID or processing not completed."}, status_code=404)
    except IOError as e:
        logging.error(f"File I/O error while creating ZIP for session {session_id}: {e}")
        return JSONResponse(content={"error": "Failed to read or write ZIP file."}, status_code=500)
    except Exception as e:
        logging.error(f"An unexpected error occurred while creating the ZIP file for session {session_id}: {e}")
        return JSONResponse(content={"error": f"An unexpected error occurred while creating the ZIP file: {e}"}, status_code=500)



@app.on_event("shutdown")
async def shutdown_event():
    """
    Cleans up the temporary predictions directory during application shutdown.

    This function is triggered when the application is about to shut down. It ensures that all files 
    in the temporary predictions directory are removed to prevent the accumulation of stale data and 
    to free up system resources. The function handles files and directories, ensuring that the 
    directory is empty before the application completely shuts down.

    Raises:
    - Exception: Logs an error if any issues occur during the cleanup process. This includes problems 
      with deleting files or directories, which might be due to permission issues or files being locked.

    Note:
    This is a critical maintenance task that helps in managing storage efficiently and avoids potential 
    data leaks between sessions. It is part of the application's lifecycle management.
    """
    try:

        # Iterate over and delete all files in the directory
        for filename in os.listdir(temp_predictions_dir):
            file_path = os.path.join(temp_predictions_dir, filename)
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)

    except Exception as e:
        logging.error(f"An error occurred during shutdown cleanup: {e}")
