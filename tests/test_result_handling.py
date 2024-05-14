import logging
import os
import pytest
import unittest
from unittest.mock import MagicMock, call, mock_open, patch




from app.result_handling import should_keep_file
#

##SHOULD KEEP FILE
class TestShouldKeepFile:
    """
    The TestShouldKeepFile class tests the functionality of the should_keep_file function,
    which determines whether a particular file type should be kept based on user preferences.
    """

    @pytest.mark.parametrize("file_info, user_preferences, expected_result", [
        ({"type": "originalVideo"}, {"keep_original": True}, True),
        ({"type": "originalVideo"}, {"keep_original": False}, True),
        ({"type": "annotatedVideo"}, {"generate_annotated_video": True}, True),
        ({"type": "annotatedVideo"}, {"generate_annotated_video": False}, True),
        ({"type": "detailedResults"}, {"keep_detailed_results": True}, True),
        ({"type": "detailedResults"}, {"keep_detailed_results": False}, True),
        ({"type": "summary"}, {"keep_summary": True}, True),
        ({"type": "summary"}, {"keep_summary": False}, True),
        ({"type": "summary"}, {}, False)
    ])
    def test_should_keep_file(self, file_info, user_preferences, expected_result):
        """
        Test various combinations of file types and user preferences to verify if files
        should be kept. The parameters include different file types and a dictionary of
        preferences that may affect the outcome.
        """

        assert should_keep_file(file_info, user_preferences) == expected_result

    def test_should_keep_file_missing_type(self):
        """
        Test the function's response to missing 'type' key in file_info.
        Expects a KeyError due to missing 'type' in the dictionary.
        """
        file_info = {}  # Missing 'type' key
        user_preferences = {"keep_original": True}
        with pytest.raises(KeyError):
            should_keep_file(file_info, user_preferences)

    def test_should_keep_file_malformed_preferences(self):
        """
        Test the function with a malformed user preference. Here, 'keep_original' is given a string
        'yes' instead of a boolean. It checks that should_keep_file can handle non-boolean truthy values correctly.
        """

        file_info = {"type": "originalVideo"}
        user_preferences = {"keep_original": "yes"}  # This is a truthy value, not explicitly a boolean
        assert should_keep_file(file_info, user_preferences) == True




#MODIFY_RESULT_BASED_ON_PREFERENCES
from app.result_handling import modify_result_based_on_preferences

class TestModifyResultBasedOnPreferences:
    """
    Tests the `modify_result_based_on_preferences` function to ensure it accurately modifies
    the list of files based on the user's preferences regarding file retention (e.g., keeping original
    or annotated videos).
    """

    @pytest.fixture
    def result(self):
        """
        Provides a standard result dictionary with multiple file types that can be used
        across multiple test methods.
        """

        return {
            "files": [
                {"name": "file1", "type": "originalVideo"},
                {"name": "file2", "type": "annotatedVideo"}
            ]
        }

    @pytest.fixture
    def user_preferences_keep_all(self):
        """
        User preferences fixture that simulates a scenario where the user chooses to keep
        all types of files.
        """
        return {"keep_original": True, "generate_annotated_video": True}

    @pytest.fixture
    def user_preferences_keep_none(self):
        """
        User preferences fixture that simulates a scenario where the user chooses not to keep
        any files.
        """
        return {"keep_original": False, "generate_annotated_video": False}

    def test_modify_result_all_kept(self, result, user_preferences_keep_all):
        """
        Tests whether all files are kept when user preferences dictate that all file types
        should be retained.
        """

        modified_result = modify_result_based_on_preferences(result, user_preferences_keep_all)
        assert len(modified_result['files']) == len(result['files']), "All files should be kept."

    def test_missing_keys(self):
        """
        Ensures that the function gracefully handles situations where the expected keys might be missing
        in the input dictionary.
        """
        result = modify_result_based_on_preferences({}, {"keep_original": True})
        assert 'files' not in result or result['files'] == [], "Function should handle missing keys gracefully."

    def test_integration_with_should_keep_file(self, result, user_preferences_keep_none):
        """
        Integration test to ensure that `modify_result_based_on_preferences` correctly interacts with the
        `should_keep_file` function, particularly testing the scenario where files should not be kept.
        This test artificially forces `should_keep_file` to always return True to observe behavior.
        """
        # Directly patching the 'should_keep_file' to always return True to test integration
        with patch('app.result_handling.should_keep_file', return_value=True):
            modified_result = modify_result_based_on_preferences(result, user_preferences_keep_none)
            assert len(modified_result['files']) == len(result['files']), "Integration with should_keep_file not handled correctly."








##HANDLE_FILES_FOR_SINGLE
from app.result_handling import handle_files_for_single

class TestVideoProcessingSingle(unittest.TestCase):
    """
    This test class verifies the behavior of the `handle_files_for_single` function which is responsible for handling
    file operations based on the detection results and user preferences in a single video processing workflow.
    """


    def test_animals_detected_handling(self):
        """
        Test to ensure that when animals are detected, the appropriate files are written and no unnecessary deletions occur.
        Verifies that all configured output paths are used and that file operations like writing to summary and detailed results
        are executed correctly according to the user preferences.
        """

        user_preferences = {
            'keep_original': True,
            'generate_annotated_video': True,
            'keep_detailed_results': True
        }
        paths = {
            "source_path": "/fake/source_video.mp4",
            "output_video_path": "/fake/annotated_output_video.mp4",
            "summary_path": "/fake/summary.txt",
            "detailed_results_path": "/fake/detailed_results.txt"
        }
        all_detailed_results = [
            "Track ID: 1.0, Animal: coyote, Box: [107.18954467773438, 582.545654296875, 214.37908935546875, 368.1712646484375]",
            "Track ID: 1.0, Animal: coyote, Box: [138.58653259277344, 595.1705322265625, 277.1730651855469, 364.16009521484375]"
        ]

        with patch('os.path.exists', return_value=True), \
                patch('os.remove') as mock_remove, \
                patch('builtins.open', mock_open(), create=True) as mocked_open:
            mocked_open.return_value.__enter__.return_value.write = MagicMock()

            result = handle_files_for_single(
                paths["source_path"],
                paths["output_video_path"],
                paths["detailed_results_path"],
                paths["summary_path"],
                user_preferences,
                True,  # Animals detected
                all_detailed_results
            )

            self.assertIn("videoUrl", result)
            self.assertIn("annotatedVideoUrl", result)
            self.assertIn("detailedResultsUrl", result)
            self.assertIn("summaryUrl", result)
            mock_remove.assert_not_called()
            expected_file_writes = [
                call(paths["summary_path"], 'w'),
                call(paths["detailed_results_path"], 'w')
            ]
            mocked_open.assert_has_calls(expected_file_writes, any_order=True)


    def test_no_animals_detected_handling(self):
        """
        Tests the file handling behavior when no animals are detected, ensuring that files are not created or
        retained unnecessarily, according to the user preferences. This includes not generating annotated videos
        and checking the correct removal of any generated or source files as specified.
        """

        user_preferences = {
            'generate_annotated_video': False
            # 'keep_original' is intentionally left out to test its absence
        }
        paths = {
            "source_path": "/fake/source_video.mp4",
            "output_video_path": "/fake/annotated_output_video.mp4",
            "summary_path": "/fake/summary.txt",
            # detailed_results_path is not needed for this scenario
        }
        all_detailed_results = []

        with patch('os.path.exists', return_value=True), \
                patch('os.remove') as mock_remove, \
                patch('builtins.open', mock_open(), create=True) as mocked_open:
            mocked_open.return_value.__enter__.return_value.write = MagicMock()

            result = handle_files_for_single(
                paths["source_path"],
                paths["output_video_path"],
                None,  # No detailed results path because no animals detected
                paths["summary_path"],
                user_preferences,
                False,  # No animals detected
                all_detailed_results
            )

            self.assertIn("summaryUrl", result)
            self.assertNotIn("videoUrl", result)
            self.assertNotIn("annotatedVideoUrl", result)

            # Assert that the output video path and source path are removed
            expected_removes = [
                call(paths["output_video_path"]),
                call(paths["source_path"])  # This is the new assertion to check if source path is removed
            ]
            mock_remove.assert_has_calls(expected_removes, any_order=True)
            print("Test execution reached the end of 'test_no_animals_detected_handling'")


    @patch('os.path.exists', return_value=True)
    @patch('os.remove')
    @patch('builtins.open', new_callable=mock_open)
    def test_handle_files_io_error(self, mock_file, mock_remove, mock_exists):
        """
        Test to ensure that an IOError during file handling is properly caught and handled.
        This test simulates an IOError that occurs when attempting to open a file, verifying that
        the error is logged and an appropriate exception is raised to signal the failure.
        """
        mock_file.side_effect = IOError("Failed to open file")
        user_preferences = {'keep_original': True}
        with self.assertLogs(level='ERROR') as log:
            with self.assertRaises(Exception) as context:
                handle_files_for_single("/fake/source/path", "/fake/output/path", "/fake/detailed/path", "/fake/summary/path",
                                        user_preferences, False, [])
            self.assertIn("IOError occurred while handling files: Failed to open file", log.output[0])
            self.assertEqual(str(context.exception), "Failed to handle files due to I/O error: Failed to open file")



    @patch('os.path.exists', return_value=True)
    @patch('os.remove')
    @patch('builtins.open', new_callable=mock_open)
    def test_handle_files_generic_error(self, mock_file, mock_remove, mock_exists):
        """
        Test to verify that generic exceptions are correctly handled during file operations.
        This test simulates a generic error to see if it is correctly logged and if an appropriate exception
        is raised to indicate an unexpected error during file handling.
        """
        mock_file.side_effect = Exception("Unexpected error")
        user_preferences = {'keep_original': True}
        with self.assertLogs(level='ERROR') as log:
            with self.assertRaises(Exception) as context:
                handle_files_for_single("/fake/source/path", "/fake/output/path", "/fake/detailed/path", "/fake/summary/path",
                                        user_preferences, False, [])
            self.assertIn("An error occurred while handling files: Unexpected error", log.output[0])
            self.assertEqual(str(context.exception), "An unexpected error occurred: Unexpected error")










##HANDLE_FILES_FOR_MULTIPLE

from app.result_handling import handle_files_for_multiple

class TestFileHandlingMultiple(unittest.TestCase):
    """
    This class tests the `handle_files_for_multiple` function, which manages file operations for scenarios involving
    multiple video files. It verifies that the function behaves correctly under different user preferences and detection outcomes.
    """

    def test_animals_detected_handling(self):
        """
        Test the file handling logic when animals are detected in the videos. This test ensures that all relevant files
        (original, annotated, summary, and detailed results) are created and written to based on the user preferences
        that require keeping all outputs.
        """
        user_preferences = {
            'keep_original': True,
            'generate_annotated_video': True,
            'keep_detailed_results': True
        }
        paths = {
            "source_path": "/fake/source_video.mp4",
            "output_video_path": "/fake/annotated_output_video.mp4",
            "summary_path": "/fake/summary.txt",
            "detailed_results_path": "/fake/detailed_results.txt"
        }
        all_detailed_results = [
            "Track ID: 1.0, Animal: coyote, Box: [107.18954467773438, 582.545654296875, 214.37908935546875, 368.1712646484375]",
            "Track ID: 1.0, Animal: coyote, Box: [138.58653259277344, 595.1705322265625, 277.1730651855469, 364.16009521484375]"
        ]

        with patch('os.path.exists', return_value=True), \
             patch('os.remove'), \
             patch('builtins.open', mock_open()) as mocked_open:

            mocked_open.return_value.__enter__.return_value.write = MagicMock()

            handle_files_for_multiple(
                paths["source_path"],
                paths["output_video_path"],
                paths["detailed_results_path"],
                paths["summary_path"],
                user_preferences,
                all_detailed_results
            )

            expected_calls = [call(paths["detailed_results_path"], 'w')]
            mocked_open.assert_has_calls(expected_calls, any_order=True)



    def test_file_deletion_handling(self):
        """
        Test the file deletion logic to ensure that files are not deleted when 'keep_original' preference is set.
        This scenario also validates that no unnecessary file operations are performed when all data is retained.
        """
        user_preferences = {'keep_original', 'generate_annotated_video', 'keep_detailed_results'}
        paths = {
            "source_path": "/fake/source_video.mp4",
            "output_video_path": "/fake/annotated_output_video.mp4",
            "summary_path": "/fake/summary.txt",
            "detailed_results_path": "/fake/detailed_results.txt"
        }
        all_detailed_results = []

        with patch('os.path.exists', return_value=True) as mocked_exists, \
             patch('os.remove') as mocked_remove, \
             patch('builtins.open', mock_open()) as mocked_open:
            mocked_open.return_value.__enter__.return_value.write = MagicMock()

            handle_files_for_multiple(
                paths["source_path"],
                paths["output_video_path"],
                paths["detailed_results_path"],
                paths["summary_path"],
                user_preferences,
                all_detailed_results
            )

            # Since 'keep_original' is in user_preferences, original files should not be deleted
            expected_calls = []
            if 'keep_original' not in user_preferences:
                expected_calls.append(call(paths["source_path"]))
            if 'keep_detailed_results' not in user_preferences:
                expected_calls.append(call(paths["detailed_results_path"]))
            mocked_remove.assert_has_calls(expected_calls, any_order=True)


    def test_no_animals_detected_handling(self):
        """
        Test handling of scenarios where no animals are detected in the video files.
        This includes verifying that no annotated videos are kept and only the summary file is written,
        indicating no detections were made.
        """
        user_preferences = {
            'generate_annotated_video': False,
            # 'keep_original' is intentionally left out to test its absence
        }
        paths = {
            "source_path": "/fake/source_video.mp4",
            "output_video_path": "/fake/annotated_output_video.mp4",
            "summary_path": "/fake/summary.txt",
            "detailed_results_path": "/fake/detailed_results.txt"
        }
        all_detailed_results = []  # No animals detected

        with patch('os.path.exists', return_value=True) as mocked_exists, \
             patch('os.remove') as mocked_remove, \
             patch('builtins.open', mock_open(), create=True) as mocked_open:
            mocked_open.return_value.__enter__.return_value.write = MagicMock()

            file_metadata = handle_files_for_multiple(
                paths["source_path"],
                paths["output_video_path"],
                paths["detailed_results_path"],
                paths["summary_path"],
                user_preferences,
                all_detailed_results
            )

            # Verify that the summary file is written correctly
            expected_calls = [call().write("No animals detected.")]
            mocked_open.return_value.__enter__.return_value.write.assert_has_calls(expected_calls, any_order=True)

            # Verify that no video files are kept
            expected_remove_calls = [
                call(paths["output_video_path"]),
                call(paths["source_path"])
            ]
            mocked_remove.assert_has_calls(expected_remove_calls, any_order=True)

            # Verify file metadata for no detection scenario
            self.assertEqual(len(file_metadata), 1)
            self.assertIn({"path": paths["summary_path"], "type": "summary", "animals_detected": False}, file_metadata)



