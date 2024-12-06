import os
import cv2
from PIL import Image
import matplotlib.pyplot as plt
import pandas as pd
import exercise_utils as utils
import dv_processing as dv
import numpy as np
import re


def event_to_array(event_store: dv.EventStore) -> np.ndarray:
    return np.array(list(map(lambda event: [event.x(), event.y()], event_store)))


def slicer_callback(events: dv.EventStore) -> None:
    slices.append(event_to_array(events))


def _activate_pixels(empty_image: np.ndarray, events: np.ndarray) -> np.ndarray:
    image = empty_image

    for x, y in events:
        image[y, x] = 255

    return image


def _build_image(resolution: tuple, events: np.ndarray) -> np.ndarray:
    empty_image = np.zeros((resolution[1], resolution[0]), dtype=np.uint8)

    return _activate_pixels(empty_image, events)


def detect_line_angle(resolution: tuple, events: np.ndarray) -> tuple[float, tuple] | tuple[None, None]:
    image = _build_image(resolution, events)

    lines = cv2.HoughLines(image, 1, np.pi / 180, threshold=10)

    if lines is not None:
        rho, theta = lines[0][0]
        angle_in_degrees = theta * (180 / np.pi)
        return angle_in_degrees, (rho, theta)

    return None, None


def display_events_and_line(
        resolution: tuple,
        events: np.ndarray,
        line_parameters: tuple,
        display_image: bool = False,
        save_image: bool = False,
        image_file_name: str = None,
        image_path: str = None,
) -> None:
    plt.figure(figsize=(resolution[0] / 100, resolution[1] / 100))
    plt.xlim(0, resolution[0])
    plt.ylim(resolution[1], 0)

    x, y = zip(*events)
    plt.scatter(x, y, color='blue', label='Events', s=5)

    if line_parameters is not None:
        rho, theta = line_parameters
        a = np.cos(theta)
        b = np.sin(theta)
        x0 = a * rho
        y0 = b * rho
        x1 = int(x0 + 1000 * (-b))
        y1 = int(y0 + 1000 * a)
        x2 = int(x0 - 1000 * (-b))
        y2 = int(y0 - 1000 * a)
        plt.plot([x1, x2], [y1, y2], color='red', label='Detected Line')

    plt.legend()

    if save_image:
        if image_path:
            os.makedirs(image_path, exist_ok=True)
            plt.savefig(os.path.join(image_path, image_file_name))
        else:
            plt.savefig(image_file_name)

    if display_image:
        plt.show()


def plot_angle_evolution(csv_angles_file: str) -> None:
    angles_data = pd.read_csv(csv_angles_file, header=None, names=['key', 'value'])

    plt.figure(figsize=(10, 5))
    plt.plot(np.array(angles_data['key']), np.array(angles_data['value']), linestyle='-', color='blue')
    plt.xlabel('Time steps')
    plt.ylabel('Angle (degrees)')
    plt.title('Evolution of the detected angles')
    plt.grid(True)
    plt.savefig('angles_evolution.png')
    plt.show()


def create_gif_from(images_path: str, animation_name: str) -> None:
    images = []
    file_names = sorted(os.listdir(images_path),
                        key=lambda x: int(re.findall(r'\d+', x)[0]) if re.findall(r'\d+', x) else float('inf'))
    for file_name in file_names:
        if file_name.endswith('.png'):
            file_path = os.path.join(images_path, file_name)
            images.append(Image.open(file_path))

    if images:
        images[0].save(animation_name, save_all=True, append_images=images[1:], loop=1)



if __name__ == '__main__':
    data = utils.load_data_from('dataset/dvSave-2024_11_26_11_34_19.aedat4')
    source_resolution = utils.event_stream_resolution(data)
    source_events = utils.get_events_from(data)
    slicer = dv.EventStreamSlicer()
    slices = []
    detected_angles = {}

    slicer.doEveryNumberOfEvents(800, slicer_callback)
    slicer.accept(source_events)

    for i, s in enumerate(slices):
        angle, line_params = detect_line_angle(source_resolution, s)
        detected_angles[i] = angle
        display_events_and_line(
            source_resolution,
            s,
            line_params,
            save_image=False,
            image_file_name=f'image_slice_{i}',
            image_path='images'
        )

    utils.save_dict_to_csv(detected_angles, 'detected_angles.csv')

    plot_angle_evolution('detected_angles.csv')

    create_gif_from('images', 'reference.gif')
