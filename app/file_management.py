import os
import shutil
import logging
from threading import Thread
import time
from fastapi import HTTPException 

from config import * 

def cleanup_directory(directory):
    """
    Cleans up the specified directory by removing all files and subdirectories contained within it.

    This function is invoked to ensure the specified directory is free of residual files, which might include
    temporary or intermediate files created during processing. It iterates through all items in the directory,
    deleting each one.

    Parameters:
    - directory (str): The path to the directory that needs to be cleaned up.

    Exceptions:
    - Exception: If an error occurs during the deletion of files or directories, it logs the specific file
      that caused the error and the reason for the failure. This helps in diagnosing issues related to file
      access permissions or file system errors.

    Note:
    This function does not return any value. It logs actions for each file and overall completion to aid in
    debugging and ensuring transparency in file management operations. Use this function with caution as it
    will irreversibly remove all contents of the specified directory.
    """

    logging.info(f"Starting cleanup of directory {directory}")
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
            logging.debug(f"Deleted {file_path}")
        except Exception as e:
            logging.error(f"Failed to delete {file_path}. Reason: {e}")

    logging.info(f"Cleanup completed for directory {directory}")


#FOR PRODUCTION
# This production version of save_uploaded_file uses shutil.copyfileobj to transfer data from the file object to disk.
# This method efficiently handles large files by transferring data in chunks, minimizing memory usage and enhancing performance.

def save_uploaded_file(file, session_id):
    """
    Saves an uploaded video file to the filesystem under a session-specific directory.

    This function is a critical step in handling file uploads, ensuring that each uploaded file is stored securely and uniquely identified by the session ID and its filename before processing.

    Parameters:
    - file (UploadFile): The file uploaded by the user.
    - session_id (str): The session identifier used to create a unique storage path.

    Returns:
    - str: The path where the file has been saved.

    Raises:
    - HTTPException: If the file fails to save due to I/O errors or other filesystem-related issues.
    """

    try:
        save_path = os.path.join(temp_predictions_dir, f'{session_id}_{file.filename}')
        with open(save_path, 'wb') as buffer:
            shutil.copyfileobj(file.file, buffer)
        return save_path
    except IOError as e:
        logging.error(f"Failed to save file {file.filename} for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save file due to I/O error.")
    except Exception as e:
        logging.error(f"Unexpected error occurred when saving file {file.filename} for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred when saving the file.")



#FOR TESTS
# This version of save_uploaded_file is specifically used for testing purposes.
# It reads all bytes from the file into memory to simplify mocking and ensure complete control over file I/O.

#def save_uploaded_file(file, session_id):
#    try:
#        # Construct the path where the file will be saved
#        save_path = os.path.join('temp_predictions_file', f'{session_id}_{file.filename}')
#        logging.info(f"Attempting to save file at {save_path}")
#
#        # Open the file in write-binary mode
#        with open(save_path, 'wb') as buffer:
#            # Ensure the file object is at the start if previously read
#            file.file.seek(0)
#            bytes_to_write = file.file.read()
#
#            # Log the amount of data read
#            logging.debug(f"Read {len(bytes_to_write)} bytes from file object.")
#
#            # Write the data to the file
#            buffer.write(bytes_to_write)
#            logging.info("File has been written to disk.")
#
#        # Return the path where the file was saved
#        return save_path
#
#    except IOError as e:
#        # Log the error and raise an HTTPException with status code 500
#        logging.error(f"Failed to save file {file.filename} for session {session_id}: {e}")
#        raise HTTPException(status_code=500, detail="Failed to save file due to I/O error.")
#
#    except Exception as e:
#        # Log any other unexpected errors and raise an HTTPException with status code 500
#        logging.error(f"Unexpected error occurred when saving file {file.filename} for session {session_id}: {e}")
#        raise HTTPException(status_code=500, detail="An unexpected error occurred when saving the file.")
#

