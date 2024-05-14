import io
import json
import pytest
import zipfile
from unittest.mock import MagicMock, call, mock_open, patch
from zipfile import ZIP_DEFLATED, ZipFile


#import pytest
#
#
#import io
#import json
#from unittest.mock import mock_open, patch, MagicMock
#import zipfile
#from zipfile import ZipFile, ZIP_DEFLATED
#import pytest
#import json
#import io
#from unittest.mock import patch, mock_open, MagicMock
#from zipfile import ZipFile, ZIP_DEFLATED
#from unittest.mock import patch, mock_open
#
## Assuming `save_manifest` is in a module named `zip_json`
#from app.zipping_json import save_manifest
#from unittest.mock import mock_open, patch, call
#import json
#
#
#import pytest
#from unittest.mock import mock_open, patch, MagicMock
#import json





from app.zipping_json import save_manifest 
#SAVE_MANIFEST
def test_save_manifest_success():
    expected_data = {
        "preferences": sorted(["preference1", "preference2"]),
        "files": ["file1", "file2"]
    }
    with patch("builtins.open", mock_open()) as mocked_file:
        save_manifest("output_dir", "123456", {"preference1", "preference2"}, ["file1", "file2"])
        mocked_file.assert_called_once_with("output_dir/123456_manifest.json", "w")
        # Correctly concatenate strings from write calls
        written_data = ''.join(call_args[0][0] for call_args in mocked_file().write.call_args_list)
        loaded_data = json.loads(written_data)
        loaded_data['preferences'] = sorted(loaded_data['preferences'])  # Ensure the order is consistent before comparison
        assert loaded_data == expected_data



def test_save_manifest_io_error():
    with patch("builtins.open", mock_open()) as mocked_file:
        mocked_file.side_effect = IOError("Failed to write")
        with pytest.raises(IOError) as exc_info:
            save_manifest("output_dir", "123456", {"preference1"}, ["file1"])
        assert "Failed to write" in str(exc_info.value)

def test_save_manifest_unexpected_error():
    with patch("builtins.open", mock_open()) as mocked_file:
        mocked_file.side_effect = Exception("Unexpected")
        with pytest.raises(Exception) as exc_info:
            save_manifest("output_dir", "123456", {"preference1"}, ["file1"])
        assert "Unexpected" in str(exc_info.value) or "An unexpected error occurred during manifest saving." in str(exc_info.value)

def test_save_manifest_empty_data():
    """Test saving a manifest with empty data lists."""
    expected_data = {"preferences": [], "files": []}
    with patch("builtins.open", mock_open()) as mocked_file:
        save_manifest("output_dir", "empty_data", [], [])
        written_data = ''.join(call_args[0][0] for call_args in mocked_file().write.call_args_list)
        assert json.loads(written_data) == expected_data

def test_save_manifest_special_characters():
    """Test saving a manifest with special characters."""
    special_data = {"preferences": ["üñîçødé"], "files": ["filè1.mp4", "大象.mp4"]}
    with patch("builtins.open", mock_open()) as mocked_file:
        save_manifest("output_dir", "special_chars", special_data['preferences'], special_data['files'])
        written_data = ''.join(call_args[0][0] for call_args in mocked_file().write.call_args_list)
        assert json.loads(written_data) == special_data

def test_save_manifest_permission_error():
    """Test error handling when file permission is denied."""
    with patch("builtins.open", mock_open()) as mocked_file:
        mocked_file.side_effect = PermissionError("Permission denied")
        with pytest.raises(PermissionError) as exc_info:
            save_manifest("output_dir", "123456", ["preference1"], ["file1"])
        assert "Permission denied" in str(exc_info.value)







#CREATE_ZIP_FROM_MANIFEST
from app.zipping_json import create_zip_from_manifest

def test_zip_creation_with_expected_size():
    # Setup
    session_id = '20240419185803_2c85d6af-6811-4ccc-8367-b55f8e496998'
    temp_dir = "/fake/dir"
    files_data = {
        "files": [
            {"path": "file1.txt", "animals_detected": True},
            {"path": "file2.txt", "animals_detected": False}
        ]
    }

    # Mock data setup
    manifest_data = json.dumps(files_data)
    file_contents = b"some file content"  # Simulate actual file contents to be zipped
    m_open = mock_open(read_data=manifest_data)
    m_open.side_effect = [
        mock_open(read_data=manifest_data).return_value,  # Reading the manifest
        mock_open(read_data=file_contents).return_value   # Reading file contents for each file
    ]

    # Patch the open and os.path.exists calls
    with patch("builtins.open", m_open), patch("os.path.exists", return_value=True), patch("zipfile.ZipFile") as mock_zip:
        mock_zip.return_value.__enter__.return_value = MagicMock(spec=zipfile.ZipFile)
        mock_zip.return_value.__enter__.return_value.write = MagicMock()

        # Function call
        zip_bytes = create_zip_from_manifest(session_id, temp_dir)

        # Check the zipfile was created and has content
        assert not zip_bytes.getvalue() == b"", "ZIP should not be empty"
        # Assert that the size of the ZIP file's content is as expected
        assert len(zip_bytes.getvalue()) == 28264747, "ZIP content size does not match expected"



def test_zip_creation_with_expected_size():
    # Setup
    session_id = "20240419185803_2c85d6af-6811-4ccc-8367-b55f8e496998"
    temp_dir = "temp_predictions_file"
    files_data = {
        "files": [
            {"path": "file1.txt", "animals_detected": True},
            {"path": "file2.txt", "animals_detected": False}
        ]
    }

    manifest_data = json.dumps(files_data)
    file_contents = b"some file content"

    # Prepare mock for open and file contents
    m_open = mock_open(read_data=manifest_data)
    m_open.side_effect = [
        mock_open(read_data=manifest_data).return_value,
        mock_open(read_data=file_contents).return_value
    ]

    # Patching open and os.path.exists
    with patch("builtins.open", m_open), patch("os.path.exists", return_value=True):
        with patch("zipfile.ZipFile") as mock_zip:
            # Setup the BytesIO object and attach it to the mock
            zip_bytes_io = io.BytesIO()
            mock_zip.return_value.__enter__.return_value = MagicMock(spec=ZipFile)

            # Patching the write method to simulate file writing
            def fake_write(file_path, arcname=None):
                # This will simulate writing content to the zip
                # by writing the file contents directly to the BytesIO object
                zip_bytes_io.write(b"Content of " + bytes(arcname, 'utf-8') if arcname else file_contents)

            # Attach the fake write method to the zipfile write call
            mock_zip.return_value.__enter__.return_value.write = fake_write

            # Function call
            create_zip_from_manifest(session_id, temp_dir)

            # Ensure the BytesIO object is not empty
            assert len(zip_bytes_io.getvalue()) > 0, "ZIP should not be empty"
            print("Size of ZIP in bytes:", len(zip_bytes_io.getvalue()))






def test_zip_creation_manifest_not_found():
    session_id = '20240419185803_2c85d6af-6811-4ccc-8367-b55f8e496998'
    temp_dir = "/fake/dir"

    # Ensure that the path does not exist
    with patch("os.path.exists", return_value=False):
        with pytest.raises(FileNotFoundError) as excinfo:
            create_zip_from_manifest(session_id, temp_dir)

    # Check the exception message to match the expected FileNotFoundError message
    assert "No such file or directory" in str(excinfo.value), "FileNotFoundError not raised for missing manifest"


#def test_zip_creation_manifest_not_found():
#    session_id = "123456789"
#    temp_dir = "/fake/dir"
#    
#    # Patch the os.path.exists to return False simulating file not found
#    with patch("os.path.exists", return_value=False), \
#         pytest.raises(FileNotFoundError) as excinfo:
#        create_zip_from_manifest(session_id, temp_dir)
#    
#    assert "Manifest file not found" in str(excinfo.value), "FileNotFoundError not raised for missing manifest"




def test_zip_creation_io_error():
    session_id = '20240419185803_2c85d6af-6811-4ccc-8367-b55f8e496998'
    temp_dir = "/fake/dir"
    files_data = {"files": [{"path": "file1.txt", "animals_detected": True}]}
    manifest_data = json.dumps(files_data)
    
    m_open = mock_open(read_data=manifest_data)
    
    with patch("builtins.open", m_open), \
         patch("os.path.exists", return_value=True), \
         patch("zipfile.ZipFile", side_effect=IOError("Disk full")):
        with pytest.raises(IOError) as excinfo:
            create_zip_from_manifest(session_id, temp_dir)
    
    assert "Disk full" in str(excinfo.value), "IOError not properly handled"

import json
from unittest.mock import mock_open, patch
import pytest

def test_zip_creation_unexpected_error():
    session_id = '20240419185803_2c85d6af-6811-4ccc-8367-b55f8e496998'
    temp_dir = "/fake/dir"
    files_data = {"files": [{"path": "file1.txt", "animals_detected": True}]}
    manifest_data = json.dumps(files_data)

    m_open = mock_open(read_data=manifest_data)

    with patch("builtins.open", m_open), \
         patch("os.path.exists", return_value=True), \
         patch("zipfile.ZipFile", side_effect=Exception("Unexpected error")):
        with pytest.raises(Exception) as excinfo:
            create_zip_from_manifest(session_id, temp_dir)

    assert "Unexpected error" in str(excinfo.value), "Generic exception not properly handled"




