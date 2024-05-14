import pytest
import logging
import os
from datetime import datetime
import uuid

from unittest.mock import patch, MagicMock
import cv2

from ultralytics import YOLO

from config import *
from app.initialization import initialize_video_processing,setup_file_paths

@patch('app.initialization.cv2.VideoCapture')
@patch('app.initialization.setup_file_paths', return_value=('path_to_video.mp4', 'path_to_detailed.txt', 'path_to_summary.txt'))
class TestVideoProcessing:
    """
    TestVideoProcessing class handles the testing of video processing functionalities within the application.
    It ensures that the video file handling, capturing, and processing are functioning as expected under various conditions.
    """

    @patch('app.initialization.cv2.VideoWriter', return_value=MagicMock())
    def test_video_capture_success(self, mock_writer, mock_setup_paths, mock_capture):
        """
        Test video capturing functionality successfully opens and processes a valid video file.
        Checks if the video file opens, captures frames correctly, and the VideoWriter is called as expected.
        """

        mock_capture.return_value.isOpened.return_value = True
        mock_capture.return_value.get.side_effect = [30, 1920, 1080]  # FPS, width, height
        from app import initialization
        _, cap, _, _, _, _ = initialize_video_processing('valid_video.mp4')
        assert cap.isOpened()
        mock_writer.assert_called_once()


    def test_video_capture_failure(self, mock_setup_paths, mock_capture):
        """
        Test video capturing functionality when opening a video file fails.
        Ensures that the appropriate exception is raised when the video file cannot be opened.
        """

        mock_capture.return_value.isOpened.return_value = False
        from app import initialization
        with pytest.raises(RuntimeError) as excinfo:
            initialize_video_processing('invalid_video.mp4')
        assert 'Cannot open the video file' in str(excinfo.value), "Error message should correctly reflect the inability to open the video file"


    def test_cleanup_on_failure(self, mock_setup_paths, mock_capture):
        """
        Test the cleanup functionality when video capture encounters an error.
        Ensures that all resources are properly released and cleaned up after a failure to get video properties.
        """

        mock_capture.return_value.isOpened.return_value = True
        mock_capture.return_value.get.side_effect = Exception("Failed to get video properties")
        from app import initialization
        with pytest.raises(RuntimeError):
            initialize_video_processing('valid_video.mp4')
        mock_capture.return_value.release.assert_called_once()  # Ensuring resources are freed






from app import initialization 


@patch('app.initialization.setup_file_paths', return_value=('path_to_video.mp4', 'path_to_detailed.txt', 'path_to_summary.txt'))
@patch('cv2.VideoWriter', return_value=MagicMock())
@patch('cv2.VideoCapture')
class TestModelLoading:
    """
    TestModelLoading class is responsible for testing the loading of machine learning models specifically for video processing.
    It ensures that models are loaded correctly under various conditions and handles errors appropriately if model loading fails.
    """
    @patch('app.initialization.YOLO', return_value=MagicMock(name='YOLO_model'))
    def test_model_loading_success(self, mock_model, mock_video_capture, mock_video_writer, mock_file_paths):
        """
        Tests successful loading of a machine learning model.
        Verifies that the model initialization call is made exactly once with the expected parameters and that a valid model object is returned.
        """
        model, _, _, _, _, _ = initialize_video_processing('dummy_source.mp4')
        mock_model.assert_called_once_with('best.pt')
        assert model is not None, "Model should not be None when loading is successful"




    @patch('app.initialization.YOLO', side_effect=Exception('Failed to load'))
    def test_model_loading_failure(self, mock_model, mock_video_capture, mock_video_writer, mock_file_paths):
        """
        Tests the error handling when the model fails to load.
        Ensures that the proper exceptions are raised and correct error messages are returned when the model cannot be loaded.
        """
        with pytest.raises(RuntimeError) as excinfo:
            initialize_video_processing('dummy_source.mp4')
        assert 'Model loading failed' in str(excinfo.value), "Error message should correctly reflect the model loading failure"






@patch('app.initialization.YOLO', return_value=MagicMock(name='YOLO_model'))
@patch('cv2.VideoCapture', return_value=MagicMock(isOpened=lambda: True))
@patch('cv2.VideoWriter', return_value=MagicMock())
class TestFilePathSetup:
    """
    TestFilePathSetup class tests the setup of file paths used in video processing.
    It aims to validate that paths are set correctly and handles errors appropriately if path setup fails.
    """
    def test_file_path_setup_failure(self, mock_writer, mock_capture, mock_model):
        """
        Tests the failure scenario for setting up file paths.
        This test ensures that an appropriate exception is raised and a meaningful error message is provided when file path setup fails.
        """

        from app import initialization
        
        # Mock setup_file_paths to raise an exception
        with patch('app.initialization.setup_file_paths', side_effect=Exception("Failed to setup file paths")):
            with pytest.raises(RuntimeError) as excinfo:
                initialization.initialize_video_processing('dummy_source.mp4')
            assert 'Error setting up file paths' in str(excinfo.value), "Error message should correctly reflect the file path setup failure"



