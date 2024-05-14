import os 
import pandas as pd 
import glob

from collections import Counter, defaultdict
import json
import logging
import zipfile
import io

#5. Summary and Reporting
def compile_and_save_summary(detailed_results, summary_path):
    """
    Compiles a summary of detailed results from video analysis and saves it to a specified path.

    This function parses detailed results from video processing, aggregates detection information by track ID, and compiles a summary report. The summary identifies the most common animal detected for each track ID and provides a consolidated view of all detections. The summary is then written to a file for review or archival purposes.

    Parameters:
    - detailed_results (list of str): A list of strings where each string contains comma-separated details about detected animals including track ID and other metadata.
    - summary_path (str): The file path where the summary will be saved.

    Returns:
    - None: This function does not return a value but writes the summary to the specified file path.

    Raises:
    - IOError: If there is an issue writing to the file.
    - Exception: If there is any issue in parsing the detailed results or generating the summary.

    The function ensures that each track's most frequently detected animal is noted, making it easy to understand the predominant detections in a video.
    """
 

    detections_by_track_id = defaultdict(list)
    for line in detailed_results:
        parts = line.split(", ")
        if len(parts) >= 2:
            track_part = parts[0].split(": ")
            animal_part = parts[1].split(": ")
            if len(track_part) == 2 and len(animal_part) == 2:
                track_id, animal_name = track_part[1], animal_part[1]
                detections_by_track_id[track_id].append(animal_name)
            else:
                logging.error(f"Data format error in line: {line}")
        else:
            logging.error(f"Insufficient data in line: {line}")

    summary_text = ["No identifiable wildlife species were detected in the video."] if not detailed_results else []
    for track_id, names in detections_by_track_id.items():
        most_common_animal, _ = Counter(names).most_common(1)[0]
        summary_text.append(f"{most_common_animal}: Detected with Track ID: {track_id}")

    with open(summary_path, 'w') as f:
        for line in summary_text:
            f.write(line + '\n')





#def compile_overall_summary(output_dir):
#    """
#    Compiles an overall summary of animal detections across multiple video analyses and saves the summary in CSV and Excel formats.
#
#    This function searches for summary files in the specified output directory, aggregates detection data across these files, and generates a concise overview of animal detections. The summary includes the video name, whether animals were detected, a list of detected animals, and their counts. The compiled data is saved in both CSV and Excel formats to facilitate easy access and analysis.
#
#    Parameters:
#    - output_dir (str): The directory where individual summary text files are stored and where the overall summary files will be saved.
#
#    Returns:
#    - tuple: A tuple containing the paths to the saved CSV and Excel summary files.
#
#    Raises:
#    - Exception: If no summary files are found in the directory or if there is an issue reading the files or saving the summaries.
#
#    The function is particularly useful in contexts where multiple video files are processed, and an aggregated report is necessary to evaluate the overall results efficiently. It ensures that the summaries are accessible in formats that are widely used for data analysis.
#    """
#
#    try:
#        summary_files = glob.glob(os.path.join(output_dir, "*_summary.txt"))
#        if not summary_files:
#            logging.warning(f"No summary files found in {output_dir}")
#            return None, None  
#
#
#        csv_path = os.path.join(output_dir, "overall_summary.csv")
#        excel_path = os.path.join(output_dir, "overall_summary.xlsx")  # Path for the Excel file
#
#        # Detected animals and their counts for each video
#        video_animals_counts = defaultdict(Counter)
#        all_video_names = set()
#
#        for summary_path in summary_files:
#            video_name = os.path.basename(summary_path).replace("_summary.txt", "")
#
#            all_video_names.add(video_name)
#            with open(summary_path, 'r', encoding='utf-8') as f:
#                for line in f:
#                    if "Detected with Track ID" in line:
#                        animal_name = line.split(":")[0].strip()
#                        video_animals_counts[video_name][animal_name] += 1
#
#        # Prepare data for DataFrame
#        data = []
#        for video_name in sorted(all_video_names):
#            animals_counts = video_animals_counts.get(video_name, Counter())
#            status = "Yes" if animals_counts else "No"
#            animals_list = ", ".join(sorted(animals_counts.keys()))
#            animal_counts_str = ", ".join([f"{animal}: {count}" for animal, count in sorted(animals_counts.items())])
#            data.append([video_name, status, animals_list, animal_counts_str])
#
#        df = pd.DataFrame(data, columns=['Video Name', 'Animals Detected', 'Detected Animals', 'Animal Counts'])
#        df.to_csv(csv_path, index=False)
#        df.to_excel(excel_path, index=False)
#
#        return csv_path, excel_path
#
#    except Exception as e:
#        logging.error(f"Failed to compile overall summary: {e}")
#        raise Exception(f"An error occurred while compiling the overall summary: {e}")
#





def compile_overall_summary(output_dir):
    """
    Compiles an overall summary of animal detections across multiple video analyses and saves the summary in CSV and Excel formats.

    This function searches for summary files in the specified output directory, aggregates detection data across these files, and generates a concise overview of animal detections. The summary includes the video name, whether animals were detected, a list of detected animals, and their counts. The compiled data is saved in both CSV and Excel formats to facilitate easy access and analysis.

    Parameters:
    - output_dir (str): The directory where individual summary text files are stored and where the overall summary files will be saved.

    Returns:
    - tuple: A tuple containing the paths to the saved CSV and Excel summary files.

    Raises:
    - Exception: If no summary files are found in the directory or if there is an issue reading the files or saving the summaries.
    """
    try:
        summary_files = glob.glob(os.path.join(output_dir, "*_summary.txt"))
        if not summary_files:
            logging.warning(f"No summary files found in {output_dir}")
            return None, None

        csv_path = os.path.join(output_dir, "overall_summary.csv")
        excel_path = os.path.join(output_dir, "overall_summary.xlsx")

        video_animals_counts = defaultdict(Counter)
        all_video_names = set()

        for summary_path in summary_files:
            filename = os.path.basename(summary_path)
            parts = filename.split('_')
            if len(parts) > 3:
                descriptive_part = parts[2]  # Third part after two UUIDs and timestamps
                video_name = descriptive_part
            else:
                video_name = filename.replace("_summary.txt", "")

            all_video_names.add(video_name)
            with open(summary_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if "Detected with Track ID" in line:
                        animal_name = line.split(":")[0].strip()
                        video_animals_counts[video_name][animal_name] += 1

        data = []
        for video_name in sorted(all_video_names):
            animals_counts = video_animals_counts.get(video_name, Counter())
            status = "Yes" if animals_counts else "No"
            animals_list = ", ".join(sorted(animals_counts.keys()))
            animal_counts_str = ", ".join([f"{animal}: {count}" for animal, count in sorted(animals_counts.items())])
            data.append([video_name, status, animals_list, animal_counts_str])

        df = pd.DataFrame(data, columns=['Video Name', 'Animals Detected', 'Detected Animals', 'Animal Counts'])
        df.to_csv(csv_path, index=False)
        df.to_excel(excel_path, index=False)

        return csv_path, excel_path

    except Exception as e:
        logging.error(f"Failed to compile overall summary: {e}")
        raise Exception(f"An error occurred while compiling the overall summary: {e}")


