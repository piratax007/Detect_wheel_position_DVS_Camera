import csv
import os.path

import cv2
import dv_processing as dv
import logging
import sys
import cv2 as cv
import numpy as np

logger = logging.getLogger()
date_time_string_format = '%Y-%m-%y %H:%M:%S'
logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format="%(asctime)s %(message)s",
    datefmt=date_time_string_format
)


def load_data_from(aedat4_file: str) -> dv.io.MonoCameraRecording:
    """
    Load data from an Aedat4 file.
    :param aedat4_file: path to the Aedat4 file as a string.
    :return: A reader containing event, frame, imu and trigger streams within the supplied aedat4 file.
    """
    reader = dv.io.MonoCameraRecording(aedat4_file)
    if not reader.isEventStreamAvailable():
        logger.critical("Something went wrong. The camera data does not have an event stream available.\n")

    return reader


def event_stream_resolution(camera_data: dv.io.MonoCameraRecording) -> tuple:
    """
    Reads the resolution of the event stream within the supplied camera data reader.
    :param camera_data: An aedat4 file reader.
    :return: width and height resolution tuple.
    """
    resolution = camera_data.getEventResolution()
    return resolution


def get_events_from(data: dv.io.MonoCameraRecording) -> dv.EventStore:
    """
    Extract the event stream from the supplied data reader.
    :param data: An aedat4 file reader.
    :return: Events contained in the supplied data reader.
    """
    events = dv.EventStore()

    while data.isRunning():
        temp_event_store = data.getNextEventBatch()
        if temp_event_store is not None:
            events.add(temp_event_store)

    return events


def _calculate_crop_origin(center: tuple[int, int], width: int = 100, height: int = 100) -> tuple[int, int]:
    origin_x = center[0] - width / 2
    origin_y = center[1] - height / 2
    return int(origin_x), int(origin_y)


def crop_centered_area(
        aedat4_file: str,
        center: tuple[int, int] = (173, 130),
        crop_width: int = 100,
        crop_height: int = 100
) -> dv.EventStore:
    """
    Crop the area of the event stream within the supplied aedat4 file to a rectangular central area.
    :param aedat4_file: path to the aedat4 file as a string.
    :param center: a tuple with the x and y coordinates of the center of the cropped area.
    :param crop_width: horizontal length of the cropped area.
    :param crop_height: vertical length of the cropped area.
    :return: An event store containing the events within the central area.
    """
    crop_origin = _calculate_crop_origin(center, crop_width, crop_height)
    region_filter = dv.EventRegionFilter((*crop_origin, crop_width, crop_height))
    region_filter.accept(get_events_from(load_data_from(aedat4_file)))
    filtered_events = region_filter.generateEvents()
    return filtered_events


def events_info(events: dv.EventStore) -> dict:
    """
    Relevant information about the given events.
    :param events: An event store
    :return: A dictionary with keys: duration, first timestamp, last time stamp and events count of the given events.
    """
    return {
        'duration': events.duration(),
        'first timestamp': events.timestamps()[0],
        'last timestamp': events.timestamps()[-1],
        'events count': events.size()
    }


def crop_preview_area(
        aedat4_file: str,
        center: tuple[int, int] = (173, 130),
        crop_width: int = 100,
        crop_height: int = 100
) -> None:
    """
    Presents a screenshot of the original event stream and the cropped area side by side.
    :param aedat4_file: path to the Aedat4 file as a string.
    :param center: a tuple with the x and y coordinates of the center of the cropped area.
    :param crop_width: horizontal length of the cropped area.
    :param crop_height: vertical length of the cropped area.
    :return: None
    """
    data = load_data_from(aedat4_file)
    source_resolution = event_stream_resolution(data)
    source_events = get_events_from(data)
    filtered_events = crop_centered_area(aedat4_file, center, crop_width, crop_height)

    visualizer = dv.visualization.EventVisualizer(source_resolution)
    visualizer_input = visualizer.generateImage(source_events)
    visualizer_output = visualizer.generateImage(filtered_events)

    preview = cv.hconcat([visualizer_input, visualizer_output])
    cv.namedWindow("preview", cv.WINDOW_NORMAL)
    cv.imshow("preview", preview)
    cv.waitKey(0)
    cv.destroyAllWindows()


def events_to_aedat4_file(
        events: dv.EventStore,
        resolution: tuple = (100, 100),
        file_name: str = 'cropped.aedat4'
) -> None:
    """
    Saves the given events to an aedat4 file.
    :param events: An event store
    :param resolution: A tuple specifying the resolution (width and height in pixels) of the given events.
    :param file_name: The file name of the generated aedat4 file.
    :return: None
    """
    config = dv.io.MonoCameraWriter.EventOnlyConfig(cameraName="DAVIS346_00000305", resolution=resolution)
    writer = dv.io.MonoCameraWriter(file_name, config)
    writer.writeEvents(events)


def handle_path(path: str) -> None:
    """
    Reads a path, if the directory does not exist, creates it.
    :param path: a directory path
    :return: None
    """
    if not os.path.exists(path):
        logger.warning(f"The directory '{path}' does not exist. Creating...")
        try:
            os.makedirs(path)
            logger.info(f"Successfully created the directory '{path}'.")
        except Exception as e:
            logger.critical(f"Failed to create the directory '{path}'. Error: {e}")


def save_dict_to_csv(data: dict, csv_file_path: str):
    path, _ = os.path.split(csv_file_path)

    handle_path(path)

    with open(csv_file_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        for key, value in data.items():
            writer.writerow([key, value])

    logger.info(f"Successfully saved the data to '{csv_file_path}'.")
