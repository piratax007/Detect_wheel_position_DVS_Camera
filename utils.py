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
        logger.warning(f"\nThe directory '{path}' does not exist. Creating...")
        try:
            os.makedirs(path)
            logger.info(f"Successfully created the directory '{path}'.")
        except Exception as e:
            logger.critical(f"Failed to create the directory '{path}'. Error: {e}")


def save_dict_to_csv(data: dict, csv_file_path: str) -> None:
    """
    Saves the given data dictionary to a CSV file with keys in the first column and values in the second column.
    :param data: a directory
    :param csv_file_path: path to the CSV file including the file name ended with '.csv'
    :return: None
    """
    path, _ = os.path.split(csv_file_path)

    handle_path(path)

    with open(csv_file_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        for key, value in data.items():
            writer.writerow([key, value])

    logger.info(f"Successfully saved the data to '{csv_file_path}'.")


def event_store_to_array(event_store: dv.EventStore) -> np.ndarray:
    """
    Converts the given event store into a numpy array.
    :param event_store: An event store
    :return: a numpy array with shape [2, 2] the x and y coordinates of the events.
    """
    return np.array(list(map(lambda event: [event.x(), event.y()], event_store)))


def _activate_pixels(empty_image: np.ndarray, events: np.ndarray) -> np.ndarray:
    """
    Assigns 255 to the entries of the empty_image corresponding to the given events array.
    :param empty_image: a zeros numpy array with shape (2, 2)
    :param events: a numpy array containing the events
    :return: a numpy array containing 255 in the inputs corresponding to the activated pixels and zero on the non activated pixels.
    """
    image = empty_image

    for x, y in events:
        image[y, x] = 255

    return image


def _build_image(resolution: tuple, events: np.ndarray) -> np.ndarray:
    empty_image = np.zeros((resolution[1], resolution[0]), dtype=np.uint8)

    return _activate_pixels(empty_image, events)


def detect_line_angle(
        resolution: tuple,
        events: np.ndarray,
        rho: int = 1,
        theta: float = np.pi / 180,
        threshold: int = 10,
) -> tuple[float, tuple] | tuple[None, None]:
    """
    Uses the Hough Lines algorithm to detect lines in the events
    :param resolution: a tuple specifying the width and height in pixels of the given events.
    :param events: a numpy array containing the events
    :param rho: The resolution of the parameter r in pixels. 1 by default.
    :param theta: The resolution of the parameter theta in degrees. 1 degree by default.
    :param threshold: The minimum number of intersection to detect a line.
    :return: a tuple containing the angle in degrees of the line and the parameter rho and theta, or a tuple containing None, None if no line is detected.
    """
    image = _build_image(resolution, events)

    lines = cv2.HoughLines(image, rho, theta, threshold=threshold)

    if lines is not None:
        rho, theta = lines[0][0]
        angle_in_degrees = theta * (180 / np.pi)
        return angle_in_degrees, (rho, theta)

    return None, None


def slice_every_events(source_events: dv.EventStore, events_per_slice: int = 800) -> list:
    """
    Create slices containing a specific number of events each slice.
    :param source_events: an event store
    :param events_per_slice: the number of events by slice
    :return: a list of slices
    """
    slicer = dv.EventStreamSlicer()
    slices = []

    def slicer_callback(events: dv.EventStore) -> None:
        slices.append(event_store_to_array(events))

    slicer.doEveryNumberOfEvents(events_per_slice, slicer_callback)
    slicer.accept(source_events)

    return slices