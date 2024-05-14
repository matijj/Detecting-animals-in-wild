# Detecting Animals In Wildlife
This repository contains a model and a sample application that utilizes object detection techniques to identify animals in wildlife footage.


<div align="center" style="padding: 10px;">
    <img src="https://github.com/matijj/new-animals-/releases/download/novi-try/racoon-POKUSAJ.gif" width="30%" style="margin-right: 15px;">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
    <img src="https://github.com/matijj/new-animals-/releases/download/novi-try/turkey-POKUSAJ.gif" width="30%" style="margin-right: 15px;">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
    <img src="https://github.com/matijj/new-animals-/releases/download/novi-try/deer-GIF.gif" width="30%">
</div>
<div align="center" style="padding-bottom: 10px;">
    <p>Videos sourced from the <a href="https://www.youtube.com/@MammalCam" target="_blank">MammalCam YouTube channel</a>.</p>
</div>


# Abstract
The "Detecting Animals in Wildlife" project is a solution designed to automate the identification and tracking of animals in wildlife footage. Utilizing state-of-the-art YOLOv8 object detection technology, this application aims to enhance the efficiency of wildlife monitoring, which is traditionally done manually through wildlife cameras, possibly saving a lot of time.

# Requirements
**Python Version**: 3.10.12
* fastapi==0.110.0
* uvicorn==0.29.0
* numpy==1.26.4
* pandas==2.2.1
* opencv-python==4.9.0.80
* pillow==10.2.0
* matplotlib==3.8.3
* seaborn==0.13.2
* pydantic==2.6.4
* httpx==0.27.0
* sqlalchemy==1.4.37  # if using databases
* pytest==8.1.1  # for testing




# DataSet
The dataset is created by me. You can access the dataset [here](https://universe.roboflow.com/assaa/4-animalz/dataset/14)



## Feedback Request
The dataset consists of images captured under various conditions (day/night, different seasons, angles), which may affect detection accuracy. If you see any false predictions, please report them. I will update model based on feedback. 


# Kind of animals (for now)
- Coyote
- Deer
- Turkey
- Raccoon
  

# Number of images
- Total images: 5932  
- Real images: 2924  
- Augmented images: 3008  

# Image Count per Category
- Deer 1318 
- Turkey 1270 
- Raccoon 954 
- Coyote 900 


<div align="center" style="padding: 10px;">
    <img src="https://github.com/matijj/new-animals-/releases/download/novi-try/image_distribution_pie_chart.png" style="width: 30%; ">
    <img src="https://github.com/matijj/new-animals-/releases/download/novi-try/animal_category_distribution_2.png" style="width: 50%; ">
</div>


# Augmentations applied:
- Flip: Horizontal, Vertical
- 90° Rotate: Clockwise, Counter-Clockwise, Upside Down
- Crop: 0% Minimum Zoom, 20% Maximum Zoom
- Rotation: Between -15° and +15°
- Shear: ±10° Horizontal, ±10° Vertical
- Grayscale: Apply to 15% of images
- Hue: Between -15° and +15°
- Saturation: Between -25% and +25%
- Brightness: Between -15% and +15%
- Exposure: Between -10% and +10%
- Blur: Up to 1.5px
- Noise: Up to 0.1% of pixels


# Trained Model
- The trained model can be found in the 'model' directory. This model uses **YOLOv8 small** for detection.

# Usage
Here is how to run app:

 ```
   uvicorn main:app
 ```

### Endpoint 1: Upload a Video for Wildlife Tracking


<div align="center" style="padding: 10px; margin-bottom: 20px;">
    <img src="https://github.com/matijj/new-animals-/releases/download/novi-try/1-endpoint-start.jpg" width="50%">
    <br>
    <hr style="border-top: 0.1px solid #ccc; margin-top: 20px; margin-bottom: 20px;">
    <img src="https://github.com/matijj/new-animals-/releases/download/novi-try/1-endpoint-end.jpg" width="50%">
</div>


**Description**: Upload a video file for automated wildlife tracking. Specify frame processing frequency.

**URL**: /upload_and_track/

**Parameters**:
- `file` (UploadFile): The video file in MP4 or AVI format.
- `preference` (str): User preferences for processing video. Options include:
  - `keep_summary`: Generate a summary of detections.
  - `generate_annotated_video`: Create an annotated video.
  - `keep_detailed_results`: Generate detailed results of detections.
- `every_n_frame` (int): Specifies the frequency of frames to process 


**Response**: Buttons to downoald annotated video, detailed results, and summary.

**Example Usage**:
```bash
curl -X 'POST' \
  'http://127.0.0.1:8000/upload_and_track/' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'file=@/path/to/your/local/repo/tests/test-video.mp4' \
  -F 'preference=keep_summary, generate_annotated_video, keep_detailed_results' \
  -F 'every_n_frame=3'
```
The `test-video.mp4` and `test-video-2.mp4` files are located inside the `tests` directory.

### Endpoint 2: Upload Multiple Videos

<div align="center" style="padding: 10px; margin-top: 30px; margin-bottom: 20px;">
    <img src="https://github.com/matijj/new-animals-/releases/download/novi-try/2-endpoint-start.jpg" width="50%">
    <br>
    <hr style="border-top: 1px solid #ccc; margin-top: 20px; margin-bottom: 20px;">
    <img src="https://github.com/matijj/new-animals-/releases/download/novi-try/2-endpoint-end.jpg" width="50%">
    <br>
    <hr style="border-top: 1px solid #ccc; margin-top: 20px; margin-bottom: 20px;">
    <img src="https://github.com/matijj/new-animals-/releases/download/novi-try/2-endpoint-zip-output.jpg" width="70%">
</div>




**Description**: Simultaneously upload and process multiple video files.

**URL**: /upload_and_track_multiple/

**Parameters**:

- `files` (List[UploadFile]): Video files in MP4 or AVI format.
- `preference` (str): Options include:
  - `keep_summary`: Generate a summary of detections.
  - `generate_annotated_video`: Create an annotated video with generated bounding boxes.
  - `keep_detailed_results`: Generate detailed results of detections.
- `every_n_frame` (int): Specifies the frequency of frames to process (e.g., every 3 frames).


**Response**: A JSON response containing the session ID, paths to the processed files (organized based on detection results), and a summary in CSV and Excel format. Errors are also returned in the response if any occur during processing.

**Summary CSV**: This file contains information about each processed video, including the video name, whether animals were detected (boolean), the categories of detected animals, and the count of each animal category.

**Example Usage**:
```bash
curl -X 'POST' \
  'http://127.0.0.1:8000/upload_and_track_multiple/' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'files=@test-video.mp4;type=video/mp4' \
  -F 'file=@/path/to/your/local/repo/tests/test-video.mp4' \
  -F 'file=@/path/to/your/local/repo/tests/test-2-video.mp4' \
  -F 'preference=keep_summary, generate_annotated_video, keep_detailed_results' \
  -F 'every_n_frame=3'

```
The `test-video.mp4` and `test-video-2.mp4` files are located inside the `tests` directory.

# Directory
<pre>
 |
 ├─app 
 │  ├── file_management.py 
 │  ├── initialization.py 
 │  ├── reporting.py <br>
 │  ├── result_handling.py 
 │  ├── video_processing.py
 |  └── zipping_json.py  
 ├─static
 │  ├── css
 │  └── js
 |─templates
 |    └── index.html
 ├─tests
 │  ├── corrupt-video.mp4
 │  ├── test-video-2.mp4
 │  ├── test-video.mp4
 │  ├── test_file_management.py
 │  ├── test_initialization.py
 │  ├── test_main.py
 │  ├── test_reporting.py
 │  ├── test_result_handling.py
 │  |── test_video_processing.py
 |   └── test_zipping_json.py
 |
 ├─main.py
 ├─config.py 
 │
 ├─model
 │  └─YOLOv8_small.pt
</pre>




# License
Animals Wildlife Detection is under [MIT license](https://en.wikipedia.org/wiki/MIT_License).




