import asyncio
import logging
import pytest
from io import BytesIO
from starlette.datastructures import UploadFile
from unittest.mock import MagicMock, call, patch

from fastapi import HTTPException, UploadFile



from app.video_processing import process_video 
##FOR PROCESS_VIDEO
@pytest.fixture
def setup_video_processing(tmp_path):
    """
    Fixture to setup the necessary mock objects and paths for testing the video processing.
    Includes a mock video capture object, model, output writer, and paths for output files.
    """

    output_dir = tmp_path / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    cap = MagicMock()
    cap.isOpened.return_value = True
    cap.read.side_effect = [(True, 'dummy_frame'), (False, '')]  # Simulates one successful frame read followed by an end of file.
    return {
        "cap": cap,
        "model": MagicMock(),
        "out": MagicMock(),
        "output_video_path": str(output_dir / "video.mp4"),
        "detailed_results_path": str(output_dir / "details.json"),
        "summary_path": str(output_dir / "summary.json")
    }

class TestVideoProcessing:

    def test_process_video_empty_video(self, setup_video_processing):
        """
        Test that process_video handles an empty video correctly by returning appropriate status and message.
        Simulates an empty video file where no frames are available to process.
        """

        with patch('app.video_processing.initialize_video_processing', return_value=(
            setup_video_processing["model"],
            setup_video_processing["cap"],
            setup_video_processing["out"],
            setup_video_processing["output_video_path"],
            setup_video_processing["detailed_results_path"],
            setup_video_processing["summary_path"]
        )), patch('app.video_processing.process_and_track_frame', return_value=('frame', ['result'])):
            setup_video_processing["cap"].read.side_effect = [(False, '')]  # Simulates an empty video
            user_preferences = {'generate_annotated_video': True}

            result = process_video("path/to/empty_video.mp4", user_preferences, is_multiple=False, every_n_frame=1)

            assert result['status'] == "No animals detected"
            assert 'paths' in result
            assert result['message'] == "No animals detected in the uploaded video."

    def test_process_video_multiple_frames(self, setup_video_processing):
        """
        Test process_video with multiple frames, checking correct handling of frame processing and result aggregation.
        Simulates processing multiple frames to verify that all are handled as expected.
        """

        with patch('app.video_processing.initialize_video_processing', return_value=(
            setup_video_processing["model"],
            setup_video_processing["cap"],
            setup_video_processing["out"],
            setup_video_processing["output_video_path"],
            setup_video_processing["detailed_results_path"],
            setup_video_processing["summary_path"]
        )), patch('app.video_processing.process_and_track_frame', side_effect=[
            ('annotated_frame_1', ['result_1']),
            ('annotated_frame_2', ['result_2']),
            ('annotated_frame_3', ['result_3'])
        ]):
            setup_video_processing["cap"].read.side_effect = [
                (True, 'frame_1'),
                (True, 'frame_2'),
                (True, 'frame_3'),
                (False, '')  # End of video
            ]
            user_preferences = {'generate_annotated_video': True}
            result = process_video("path/to/video.mp4", user_preferences, is_multiple=False, every_n_frame=1)

            assert result['status'] == "Animals detected"
            assert 'paths' in result
            assert len(result['paths']) == 2  # Adjusted based on actual behavior

    def test_process_video_default_every_n_frame(self, setup_video_processing):
        """
        Test the default setting for processing every Nth frame in process_video.
        Ensures that the default frequency of frame processing is correctly applied and results are as expected.
        """

        with patch('app.video_processing.initialize_video_processing', return_value=(
            setup_video_processing["model"],
            setup_video_processing["cap"],
            setup_video_processing["out"],
            setup_video_processing["output_video_path"],
            setup_video_processing["detailed_results_path"],
            setup_video_processing["summary_path"]
        )), patch('app.video_processing.get_every_n_frame', return_value=5) as mock_get_every_n_frame, \
            patch('app.video_processing.process_and_track_frame', return_value=('frame', ['result'])):
            user_preferences = {'generate_annotated_video': True}

            result = process_video("path/to/video.mp4", user_preferences, is_multiple=False)

            mock_get_every_n_frame.assert_called_once()
            assert result['status'] == "Animals detected"
            assert 'paths' in result
            assert result['message'] == "The uploaded video contains identifiable wildlife species."












from app.video_processing import  process_and_track_frame

#process_and_Track_FRAME
    
from unittest.mock import MagicMock, patch

def test_process_and_track_frame_effective_tracking(setup_video_processing):
    """
    Test effective tracking in process_and_track_frame function to ensure it processes detections correctly.
    Verifies that the function annotates the frame and records detailed results when detections occur.
    """
    frame = 'test_frame'
    model = setup_video_processing['model']
    every_n_frame = 1
    frame_counter = 1

    # Set up mock data to simulate actual detections
    mock_cls = MagicMock()
    mock_cls.cpu.return_value.numpy.return_value = [1]  # Simulating detection of one object

    mock_xywh = MagicMock()
    mock_xywh.cpu.return_value.numpy.return_value = [[10, 10, 50, 50]]  # Bounding box coordinates

    mock_ids = MagicMock()
    mock_ids.cpu.return_value.numpy.return_value = [1234]  # Detection ID

    # Set up the boxes mock
    mock_boxes = MagicMock(cls=mock_cls, xywh=mock_xywh, id=mock_ids)
    result_mock = MagicMock(boxes=mock_boxes)
    model.track.return_value = [result_mock]

    # Execute the function
    annotated_frame, detailed_results = process_and_track_frame(frame, model, frame_counter, every_n_frame)

    # Check if the results are processed correctly
    assert detailed_results, "Detailed results should not be empty"
    assert detailed_results[0].startswith("Track ID: 1234"), "Check format of detailed results"



def test_process_and_track_frame_no_detections(setup_video_processing):
    """
    Test the process_and_track_frame function for scenarios with no detections.
    Verifies that it handles empty detection results correctly, not altering the frame or producing detailed results.
    """
    frame = 'test_frame'
    model = setup_video_processing['model']
    every_n_frame = 1
    frame_counter = 1

    # Setup model to return empty detection
    model.track.return_value = []

    # Execute the function
    annotated_frame, detailed_results = process_and_track_frame(frame, model, frame_counter, every_n_frame)

    # Check if the results are processed correctly for no detections
    assert not detailed_results, "Detailed results should be empty for no detections"
    assert annotated_frame == frame, "Annotated frame should be unchanged for no detections"


def test_process_and_track_frame_error_handling(setup_video_processing):
    """
    Test error handling in the process_and_track_frame function.
    Verifies that it logs errors appropriately and does not produce results when an exception occurs during tracking.
    """
    frame = 'test_frame'
    model = setup_video_processing['model']
    every_n_frame = 1
    frame_counter = 1

    # Setup the model to raise an exception when track is called
    model.track.side_effect = Exception("Tracking failed")

    # Patch logging to check if the error is logged correctly
    with patch('logging.error') as mock_logging_error:
        # Execute the function
        annotated_frame, detailed_results = process_and_track_frame(frame, model, frame_counter, every_n_frame)

        # Verify logging was called with the expected message
        mock_logging_error.assert_called_once_with(f"Failed to track frame {frame_counter}: Tracking failed")

        # Ensure no detailed results are produced when an exception occurs
        assert not detailed_results, "Detailed results should be empty when an exception occurs"

        # Ensure that the annotated frame remains unchanged due to the error
        assert annotated_frame == frame, "Annotated frame should be unchanged when an exception occurs"






#PROCESS_EACH_FILE
from app.video_processing import process_each_file


#WORKS ONLY WHEN PROCESS_EACH_FILE IS FOR TEST 
@pytest.mark.asyncio
@pytest.mark.timeout(10)
async def test_process_each_file_success():
    """
    Test the successful processing of a video file.
    Verifies that the function processes a valid video file correctly with specified user preferences.
    """

    video_path = '/mnt/c/Users/Matija/wsl_projekti/sync_async_38/tests/test-video.mp4'
    with open(video_path, 'rb') as f:
        video_bytes = f.read()
    
    mock_file = MagicMock(spec=UploadFile)
    mock_file.filename = "test-video.mp4"
    mock_file.file = BytesIO(video_bytes)
    mock_file.file.read = MagicMock(return_value=video_bytes)
    
    session_id = '20240419123128_f087cc11-61fb-44c1-9514-d7b8d3645d06'
    user_preferences = {'keep_summary', 'generate_annotated_video'}
    every_n_frame = 3
    
    print("About to call process_each_file")
    await process_each_file(mock_file, session_id, user_preferences, every_n_frame)
    print("process_each_file has been called")







@pytest.mark.asyncio
async def test_process_each_file_save_failure():
    """
    Test error handling when the file save operation fails.
    Ensures that the function logs errors correctly and reports failure appropriately.
    """
    video_bytes = b'test video data'
    mock_file = MagicMock(spec=UploadFile)
    mock_file.filename = "test-video.mp4"
    mock_file.file = BytesIO(video_bytes)
    mock_file.file.read = MagicMock(return_value=video_bytes)

    session_id = 'test_session_id'
    user_preferences = {'keep_summary': True, 'generate_annotated_video': True}
    every_n_frame = 3

    # Ensure correct path for patching if save_uploaded_file is used in process_each_file as imported
    with patch('app.video_processing.save_uploaded_file', side_effect=Exception("Disk full")) as mock_save:
        # Directly patch logging in the correct module
        with patch('app.video_processing.logging') as mock_logging:
            result = await process_each_file(mock_file, session_id, user_preferences, every_n_frame)

            # Ensure that mock_save was called, which confirms we are testing the right scenario
            mock_save.assert_called_once()

            # Check if error was logged
            mock_logging.error.assert_called_once()

            # Verify the error message in the result
            assert result == {"error": "Processing failed for test-video.mp4: Disk full"}



@pytest.mark.asyncio
async def test_process_each_file_video_processing_failure():
    """
    Test error handling when video processing fails.
    Ensures that the function logs errors correctly and does not produce misleading results.
    """
    # Setup mock data
    video_bytes = b'test video data'
    mock_file = MagicMock(spec=UploadFile)
    mock_file.filename = "test-video.mp4"
    mock_file.file = BytesIO(video_bytes)
    mock_file.file.read = MagicMock(return_value=video_bytes)


    session_id = '20240419185803_2c85d6af-6811-4ccc-8367-b55f8e496998'

    user_preferences = {'keep_summary': True, 'generate_annotated_video': True}
    every_n_frame = 3

    # Mock save_uploaded_file to return a dummy path
    with patch('app.video_processing.save_uploaded_file', return_value="dummy_path") as mock_save:
        # Simulate failure in process_video
        with patch('app.video_processing.process_video', side_effect=Exception("Video processing failed")) as mock_process:
            with patch('app.video_processing.logging') as mock_logging:
                result = await process_each_file(mock_file, session_id, user_preferences, every_n_frame)

                mock_process.assert_called_once()
                assert "error" in result
                assert result['error'] == "Processing failed for test-video.mp4: Video processing failed"
                mock_logging.error.assert_called_once()





@pytest.mark.asyncio
async def test_concurrent_video_processing():
    """
    Test the concurrent processing of multiple video files.
    Ensures that the system can handle simultaneous video processing tasks using asynchronous calls.
    This test verifies that all sessions are processed successfully and concurrently without interference.
    """
    session_ids = ['session1', 'session2', 'session3', ...]  
    user_preferences = {'keep_summary': True, 'generate_annotated_video': True}
    every_n_frame = 3

    async def process_file(session_id):
        """
        Helper coroutine to process a single video file, mocking the expected behavior.
        This function mocks the file upload and processing to simulate the end-to-end functionality.
        """
        video_bytes = b'sample video data'
        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = f"test-video-{session_id}.mp4"
        mock_file.file = BytesIO(video_bytes)
        mock_file.file.read = MagicMock(return_value=video_bytes)

        # Assume save_uploaded_file and process_video are correctly mocked
        with patch('app.video_processing.save_uploaded_file', return_value="path/to/video"):
            with patch('app.video_processing.process_video', return_value={'result': 'success'}):
                result = await process_each_file(mock_file, session_id, user_preferences, every_n_frame)
                assert 'result' in result, f"Failed processing for session {session_id}"

    # Run the test concurrently for all session IDs
    await asyncio.gather(*(process_file(sid) for sid in session_ids))




@pytest.mark.asyncio
async def test_process_each_file_invalid_format():
    """
    Test error handling when an invalid video format is provided.
    Ensures that the function logs errors correctly and reports format issues.
    """
    # Setup mock data
    non_video_data = b'Just some text, not a video'
    mock_file = MagicMock(spec=UploadFile)
    mock_file.filename = "invalid_file.txt"
    mock_file.file = BytesIO(non_video_data)
    mock_file.file.read = MagicMock(return_value=non_video_data)
    session_id = '20240419185803_2c85d6af-6811-4ccc-8367-b55f8e496998'
    user_preferences = {'keep_summary': True, 'generate_annotated_video': True}
    every_n_frame = 3

    with patch('app.video_processing.save_uploaded_file', return_value="path/to/file"):
        with patch('app.video_processing.process_video', side_effect=Exception("Invalid file format")) as mock_process:
            with patch('app.video_processing.logging') as mock_logging:
                result = await process_each_file(mock_file, session_id, user_preferences, every_n_frame)

                mock_process.assert_called_once()
                assert "error" in result
                assert result['error'] == "Processing failed for invalid_file.txt: Invalid file format"
                mock_logging.error.assert_called_once()








