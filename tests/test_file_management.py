import pytest
from unittest.mock import patch, MagicMock

from io import BytesIO
from fastapi import HTTPException



from app.file_management import cleanup_directory

#CLEANUP_DIRECTORY
def test_cleanup_directory_empty(tmp_path):
    """
    Test the cleanup_directory function on an empty directory to ensure no actions are taken.
    It verifies that neither files nor directories are deleted when the directory is empty.
    """
    with patch('os.listdir', return_value=[]), \
         patch('os.path.isfile', return_value=False), \
         patch('os.unlink') as mock_unlink, \
         patch('shutil.rmtree') as mock_rmtree:
        cleanup_directory(str(tmp_path))
        mock_unlink.assert_not_called()
        mock_rmtree.assert_not_called()


def test_cleanup_directory_with_files(tmp_path):
    """
    Test cleanup_directory to ensure it correctly removes files and directories.
    This tests the function's ability to handle a directory with mixed contents.
    """
    # Setup: Create a file and a directory in the temporary directory
    (tmp_path / "file1.txt").write_text("content")
    (tmp_path / "dir1").mkdir()
    # Patch listdir and isfile to control directory contents and file identification
    with patch('os.listdir', return_value=["file1.txt", "dir1"]), \
         patch('os.path.isfile', side_effect=lambda x: x.endswith(".txt")), \
         patch('os.unlink') as mock_unlink, \
         patch('shutil.rmtree') as mock_rmtree:
        cleanup_directory(str(tmp_path))  # Action: Perform the cleanup operation
        mock_unlink.assert_called_once_with(str(tmp_path / "file1.txt"))  # Assert: File is deleted
        mock_rmtree.assert_called_once_with(str(tmp_path / "dir1"))       # Assert: Directory is removed

def test_cleanup_directory_permission_error(tmp_path):
    """
    Test cleanup_directory's response to a PermissionError when attempting to delete a file.
    This checks the function's error handling capabilities for file deletion operations.
    """
    # Setup: Create a file in the temporary directory
    (tmp_path / "file1.txt").write_text("content")
    # Patch listdir and isfile to simulate directory content and file detection,
    # and patch unlink to throw a PermissionError
    with patch('os.listdir', return_value=["file1.txt"]), \
         patch('os.path.isfile', return_value=True), \
         patch('os.unlink', side_effect=PermissionError("No permission")) as mock_unlink, \
         patch('logging.error') as mock_log_error:
        cleanup_directory(str(tmp_path))  # Action: Attempt cleanup, expecting an error
        mock_unlink.assert_called_once_with(str(tmp_path / "file1.txt"))  # Assert: Deletion attempt was made
        mock_log_error.assert_called()  # Assert: Error logging was triggered




#SAVE_UPLOADED_FILE
from app.file_management import save_uploaded_file

@pytest.fixture
def file_mock():
    """
    Fixture to create a mock file object.
    Simulates an uploaded file with a predefined filename and content.
    """
    mock = MagicMock()
    mock.filename = "test_video.mp4"
    mock.file = MagicMock(spec=BytesIO)
    mock.file.read.return_value = b"content of the file"
    return mock

##DOESNT WORK WHEN FROM APP.VIDEO_PROCESSING.SAVE_UPLOADED_FILE IS FOR TEST 
##WHEN ITS FOR PRODUCTION IT WORKS 
#def test_save_uploaded_file_success(file_mock, tmp_path):
#    session_id = "123456"
#    
#    with patch('os.path.join', return_value=str(tmp_path / f"{session_id}_{file_mock.filename}")), \
#         patch('builtins.open', new_callable=MagicMock) as mock_open, \
#         patch('shutil.copyfileobj') as mock_copyfileobj:
#        mock_file_handle = mock_open.return_value.__enter__.return_value
#        
#        save_path = save_uploaded_file(file_mock, session_id)
#        
#        assert save_path == str(tmp_path / f"{session_id}_{file_mock.filename}")
#        mock_copyfileobj.assert_called_once_with(file_mock.file, mock_file_handle)
#




def test_save_uploaded_file_io_error(file_mock, tmp_path):
    """
    Test save_uploaded_file function to ensure it raises an HTTPException when an I/O error occurs.
    This simulates an error during the file write operation.
    """

    session_id = "123456"
    
    with patch('os.path.join', return_value=str(tmp_path / f"{session_id}_{file_mock.filename}")), \
         patch('builtins.open', side_effect=IOError("Failed to write file")), \
         pytest.raises(HTTPException) as excinfo:
        save_uploaded_file(file_mock, session_id)
    
    assert "Failed to save file due to I/O error" in str(excinfo.value.detail)

def test_save_uploaded_file_unexpected_error(file_mock, tmp_path):
    """
    Test save_uploaded_file function for handling of non-specific exceptions.
    Ensures that any unexpected errors are also caught and an appropriate HTTPException is raised.
    """
    session_id = "123456"
    
    with patch('os.path.join', return_value=str(tmp_path / f"{session_id}_{file_mock.filename}")), \
         patch('builtins.open', side_effect=Exception("Unexpected error")), \
         pytest.raises(HTTPException) as excinfo:
        save_uploaded_file(file_mock, session_id)
    
    assert "An unexpected error occurred when saving the file" in str(excinfo.value.detail)







