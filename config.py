# in config.py
import os

class_id_to_name = {
    0: 'coyote',
    1: 'deer',
    2: 'raccoon',
    3: 'turkey'
}


def get_every_n_frame(default=3):
    return int(os.getenv('EVERY_N_FRAME', default))


temp_predictions_dir = os.getenv('TEMP_PREDICTIONS_DIR', 'temp_predictions_file')
static_files_dir = os.getenv('STATIC_FILES_DIR', 'static')
templates_dir = os.getenv('TEMPLATES_DIR', 'templates')

output_video_dir = os.getenv('OUTPUT_VIDEO_DIR', 'temp_predictions_file')
output_dir = os.getenv('OUTPUT_DIR', 'temp_predictions_file')




