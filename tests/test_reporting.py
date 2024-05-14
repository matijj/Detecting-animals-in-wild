import os
import unittest

import pandas as pd
import pytest
from collections import Counter, defaultdict
from unittest.mock import MagicMock, mock_open, patch, call

from app.video_processing import process_video


from app.reporting import compile_and_save_summary

#COMPILE_AND_SAVE_SUMMARY
def test_compile_and_save_summary_with_valid_data(tmp_path):
    """
    Test that compile_and_save_summary correctly processes and formats valid detailed results.
    Verifies the function outputs a correctly formatted summary file based on input data.
    """
    detailed_results = [
        "Track ID: 1, Animal: Deer",
        "Track ID: 1, Animal: Deer",
        "Track ID: 2, Animal: Coyote"
    ]
    summary_path = tmp_path / "summary.txt"

    compile_and_save_summary(detailed_results, str(summary_path))

    with open(summary_path, 'r') as file:
        content = file.readlines()
    
    assert content == [
        "Deer: Detected with Track ID: 1\n",
        "Coyote: Detected with Track ID: 2\n"
    ]


def test_compile_and_save_summary_with_insufficient_data(caplog, tmp_path):
    """
    Test that compile_and_save_summary handles insufficient data by logging an appropriate error message.
    Ensures that the function does not crash or behave unpredictably when data lacks necessary details.
    """

    detailed_results = ["Track ID: 1"]
    summary_path = tmp_path / "summary.txt"

    compile_and_save_summary(detailed_results, str(summary_path))

    assert "Insufficient data in line: Track ID: 1" in caplog.text

def test_compile_and_save_summary_with_format_errors(caplog, tmp_path):
    """
    Test that compile_and_save_summary captures and logs format errors in input data.
    This test ensures that format issues are identified and appropriately logged, avoiding misinterpretation.
    """

    detailed_results = ["Track ID 1, Animal Deer"]
    summary_path = tmp_path / "summary.txt"

    compile_and_save_summary(detailed_results, str(summary_path))

    assert "Data format error in line: Track ID 1, Animal Deer" in caplog.text

def test_compile_and_save_summary_with_no_data(tmp_path):
    """
    Test that compile_and_save_summary handles a case with no detailed results.
    Checks that the function outputs a specific message when there are no data to process.
    """

    detailed_results = []
    summary_path = tmp_path / "summary.txt"

    compile_and_save_summary(detailed_results, str(summary_path))

    with open(summary_path, 'r') as file:
        content = file.read()
    
    assert content == "No identifiable wildlife species were detected in the video.\n"



#COMPILE_OVERALL_SUMMARY

from app.reporting import compile_overall_summary 

class TestCompileOverallSummary(unittest.TestCase):

    """
    Tests for the compile_overall_summary function to ensure it correctly processes summary files
    and compiles them into a single CSV and Excel document.
    """

    @patch('glob.glob', return_value=[])
    @patch('logging.warning')
    def test_no_summary_files(self, mock_warning, mock_glob):
        """
        Verify that the function handles the absence of summary files by logging a warning
        and returning None for both outputs.
        """

        output_dir = 'fake_directory'
        result = compile_overall_summary(output_dir)
        mock_warning.assert_called_once_with(f"No summary files found in {output_dir}")
        self.assertEqual(result, (None, None))

    @patch('glob.glob', return_value=['/fake_directory/video1_summary.txt'])
    @patch('builtins.open', new_callable=mock_open, read_data="Deer: Detected with Track ID: 1")
    @patch('pandas.DataFrame.to_csv')
    @patch('pandas.DataFrame.to_excel')
    def test_single_summary_file(self, mock_to_excel, mock_to_csv, mock_open, mock_glob):
        """
        Test that a single summary file is processed correctly, resulting in one call each to
        DataFrame.to_csv and DataFrame.to_excel.
        """
        output_dir = 'fake_directory'
        compile_overall_summary(output_dir)
        mock_to_csv.assert_called_once()
        mock_to_excel.assert_called_once()


    @patch('glob.glob', return_value=['/fake_directory/video1_summary.txt', '/fake_directory/video2_summary.txt'])
    @patch('os.path.basename', side_effect=lambda x: x.split('/')[-1])
    @patch('builtins.open', new_callable=mock_open, read_data="Deer: Detected with Track ID: 1")
    @patch('pandas.DataFrame.to_csv')
    @patch('pandas.DataFrame.to_excel')
    def test_multiple_summary_files(self, mock_to_excel, mock_to_csv, mocked_open, mock_basename, mock_glob):
        """
        Test the function's ability to handle multiple summary files and ensure that all files
        are opened and processed correctly.
        """
        output_dir = 'fake_directory'
        compile_overall_summary(output_dir)
        # Correctly assert calls to mocked_open
        expected_calls = [
            call('/fake_directory/video1_summary.txt', 'r', encoding='utf-8'),
            call('/fake_directory/video2_summary.txt', 'r', encoding='utf-8')
        ]
        mocked_open.assert_has_calls(expected_calls, any_order=True)

    @patch('glob.glob', return_value=['/fake_directory/video1_summary.txt'])
    @patch('builtins.open', new_callable=mock_open, read_data="Deer: Detected with Track ID: 1")
    @patch('pandas.DataFrame.to_csv', side_effect=Exception("Error writing CSV"))
    @patch('logging.error')
    def test_error_handling(self, mock_logging_error, mock_to_csv, mock_open, mock_glob):
        """
        Ensure that any exceptions during the file writing process are caught and logged appropriately,
        and the exception is raised to the caller.
        """
        output_dir = 'fake_directory'
        with self.assertRaises(Exception) as context:
            compile_overall_summary(output_dir)
        self.assertTrue('Error writing CSV' in str(context.exception))
        mock_logging_error.assert_called_with('Failed to compile overall summary: Error writing CSV')





