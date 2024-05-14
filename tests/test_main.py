import io
import json
import logging
import os

import pytest
from asynctest import CoroutineMock
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.testclient import TestClient
from httpx import AsyncClient
from starlette.responses import JSONResponse
from unittest.mock import AsyncMock, MagicMock, mock_open, patch

from config import get_every_n_frame, temp_predictions_dir  
 


from main import app


@pytest.fixture(scope="class")
def client():
    """
    Provides a test client for the application. This client can be used to make requests to the application
    for testing purposes. The fixture is scoped to the class level, so it's instantiated once per test class.
    """
    with TestClient(app) as c:
        yield c
                  




#UPLOAD_FORM
def test_upload_form(client):
    """
    Tests the initial form page load for uploading videos.
    This test ensures that the form page loads successfully with a status code of 200 and the correct content type.
    It further checks the presence of various HTML elements to confirm that the form is rendered as expected.

    Verifications include:
    - Correct page title indicating it's meant for video uploads.
    - Main heading presence to guide the user.
    - The existence of an HTML form with the appropriate enctype for file uploads.
    - Presence of a file input field designed for uploading files.
    - A submit button with the correct label.
    - Additional form elements that allow configuring processing parameters like frame intervals.
    - Optional checks for multiple video uploads to verify UI elements for batch operations.
    """
    response = client.get("/")
    assert response.status_code == 200
    assert response.headers['content-type'] == 'text/html; charset=utf-8'
    # Check for the title in the HTML
    assert "<title>Upload Videos for Wildlife Tracking</title>" in response.text
    # Check for the main heading
    assert "<h1>Upload a Video for Wildlife Tracking</h1>" in response.text
    # Check for the form and its specific elements
    assert '<form id="uploadForm" enctype="multipart/form-data">' in response.text
    # Check for specific input types like file input
    assert '<input type="file" name="file" class="file-input" required />' in response.text
    # Check for the button text
    assert '<button type="submit" class="submit-btn">Upload</button>' in response.text
    # You could also include checks for labels if you need to
    assert 'Process every N frame:' in response.text
    # Optionally, check for elements related to the second form
    assert '<h1>Upload Multiple Videos</h1>' in response.text
    assert '<input type="file" name="files" class="file-input" multiple required />' in response.text

#---------------------------------------------------------------------------------------
#


#---------------------------------------------------------------------------------------

#
#UPLOAD_AND_TRACK
@pytest.mark.usefixtures("client")  # Ensures the client fixture is used for all tests in this class
class TestUploadAndTrack:
    def test_upload_with_incorrect_file_type(self, client):
        """
        Tests the API's response to uploading a file with an incorrect file type.
        Ensures that the endpoint correctly identifies and rejects non-video files,
        returning a 400 Bad Request status with an appropriate error message.
        """
        response = client.post(
            "/upload_and_track/",
            files={"file": ("testfile.txt", "dummy content", "text/plain")},
            data={"preference": "none", "every_n_frame": 3}
        )
        assert response.status_code == 400
        assert "Invalid file type" in response.text

    def test_upload_with_correct_file_type_but_io_error(self, client):
        """
        Tests the API's behavior when an IOError occurs during file processing.
        This test simulates a failure in writing the file to disk to see if the API
        can gracefully handle such errors and communicate them properly to the client.
        """
        with patch("shutil.copyfileobj", side_effect=IOError("Failed to write")):
            response = client.post(
                "/upload_and_track/",
                files={"file": ("video.mp4", b"dummy content", "video/mp4")},
                data={"preference": "none", "every_n_frame": 3}
            )
        assert response.status_code == 500
        assert "Failed to save file." in response.text

    def test_upload_with_correct_file_type_success(self, client):
        """
        Verifies that the endpoint handles a valid video file upload successfully.
        Mocks the file saving and video processing functions to test the API's response
        under successful processing conditions, expecting a 200 OK status and a success message.
        """

        with patch("shutil.copyfileobj"), \
             patch("main.process_video", return_value={'status': 'success', 'message': 'Processing completed', 'paths': {}}):
            response = client.post(
                "/upload_and_track/",
                files={"file": ("video.mp4", b"dummy video content", "video/mp4")},
                data={"preference": "cats,dogs", "every_n_frame": 3}
            )
        assert response.status_code == 200
        assert response.json() == {
            "status": "success",
            "message": "Processing completed",
            "paths": {}
        }

    def test_upload_with_video_processing_failure(self, client):
        """
        Tests the API's error handling when there is a failure during the video processing stage.
        Simulates a scenario where processing parameters are invalid, expecting the API to return
        a 500 Internal Server Error and a specific error message indicating processing failure.
        """
        with patch("shutil.copyfileobj"), \
             patch("main.process_video", side_effect=ValueError("Invalid processing parameters")):


            response = client.post( 
                "/upload_and_track/",
                files={"file": ("video.mp4", b"dummy video content", "video/mp4")},
                data={"preference": "invalid,preferences", "every_n_frame": 3}                                                                                        )
        assert response.status_code == 500
        assert "Video processing failed" in response.text





##UPLOAD_AND_TRACK_MULTIPLE

#
#
##---------------------------------------------------------------------------------------
#

#UPLOAD_AND_TRACK_MULTIPLE

##UPLOAD_AND_TRACK_MULTIPLE
class TestUploadAndTrackMultiple:
    @pytest.mark.asyncio
    async def test_upload_with_no_files(self, client):
        """
        Tests the endpoint's behavior when no files are uploaded.
        It verifies that the server returns a 422 Unprocessable Entity status code,
        indicating that the request cannot be processed due to a lack of files.
        """
        response = client.post(
            "/upload_and_track_multiple/",
            files=[],
            data={"preference": "none", "every_n_frame": 3}
        )
        assert response.status_code == 422, "Expected 422 Unprocessable Entity status code for empty file list"
        assert "detail" in response.json(), "Expected a detailed error message indicating why the request was unprocessable"

    @pytest.mark.asyncio
    async def test_upload_with_incorrect_file_type(self, client):
        """
        Tests the system's response to files of incorrect types being uploaded.
        This test ensures that the server can correctly identify and reject unsupported file formats,
        returning a 400 Bad Request status code along with a specific error message about the invalid file type.
        """

        files = [
            ("files", ("not_a_video.txt", b"dummy content", "text/plain")),
        ]
        data = {"preference": "cats,dogs", "every_n_frame": 3}
        response = client.post("/upload_and_track_multiple/", files=files, data=data)
        assert response.status_code == 400, "Expected 400 Bad Request status code for incorrect file type"
        assert "Invalid file type" in response.json()['error'], "Expected an error message about invalid file type"

    def test_upload_and_track_multiple(self, client):
        """
        Verifies that the API correctly handles a valid video file upload,
        processing it according to the provided preferences and frame rate specifications.
        This test expects a successful 200 OK response along with the specific details of the processing results.
        """

        with open("tests/test-video-2.mp4", "rb") as video_file:
            files = {
                "files": ("test-video-2.mp4", video_file.read(), "video/mp4")  # Make sure to read the file if necessary
            }
            data = {
                "preference": "cats,dogs",
                "every_n_frame": 3
            }
            response = client.post("/upload_and_track_multiple/", files=files, data=data)
            assert response.status_code == 200, f"Failed with status {response.status_code} and detail: {response.json()}"
            # Add more checks here as needed to validate response contents

    @pytest.mark.asyncio
    async def test_upload_with_multiple_files_mixed(self, client):
        """
        Tests the endpoint's handling of a mixed file upload, containing both valid and invalid file types.
        This checks the system's ability to reject the request when any of the uploaded files are of an unsupported format,
        ensuring robust error handling and validation for bulk uploads.
        """
        files = [
            ("files", ("valid_video2.mp4", open("tests/test-video-2.mp4", "rb").read(), "video/mp4")),
            ("files", ("not_a_video.txt", b"dummy content", "text/plain")),
        ]
        data = {"preference": "cats,dogs", "every_n_frame": 3}
        response = client.post("/upload_and_track_multiple/", files=files, data=data)
        assert response.status_code == 400
        assert "Invalid file type" in response.json()['error']







#------------------------------------------------------------------------------------
#SHUTDOWN

@app.on_event("shutdown")
async def shutdown_event():
# This function is executed when the FastAPI application is shutting down.
# It writes a message to a text file indicating the application has been terminated.
    with open("shutdown-test-file.txt", "w") as fp:
        fp.write("FastAPI app has been terminated")

def test_app_shutdown():
    # This test ensures that the shutdown event correctly triggers and executes its logic.
    # Patches are used to mock the behavior of the os functions to simulate an exception during cleanup.
    with TestClient(app) as client:
        pass  # You don't need to make any actual requests

    
    assert os.path.exists("shutdown-test-file.txt"), "Shutdown file was not created"
    with open("shutdown-test-file.txt", "r") as fp:
        contents = fp.read()
    assert contents == "FastAPI app has been terminated", "File contents are incorrect"

    os.remove("shutdown-test-file.txt")


def test_app_shutdown_with_exception():
    # This test checks the robustness of the shutdown process by simulating a failure scenario.
    # Patches are used to mock the behavior of the os functions to simulate an exception during cleanup.

    with patch('os.listdir', return_value=['file1.txt']), \
         patch('os.path.isfile', side_effect=lambda x: True), \
         patch('os.path.islink', side_effect=lambda x: False), \
         patch('os.unlink', side_effect=Exception("Mocked exception")), \
         patch('logging.error') as mock_log_error:

        with TestClient(app) as client:
            pass  

        
        mock_log_error.assert_called_once()
        
        logged_message = str(mock_log_error.call_args)
        expected_message = "an error occurred during shutdown cleanup"
        assert expected_message.lower() in logged_message.lower(), "Expected message not found in the logged message"



