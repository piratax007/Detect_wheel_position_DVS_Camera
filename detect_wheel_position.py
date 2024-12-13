import os
from PIL import Image
import matplotlib.pyplot as plt
import pandas as pd
import utils
import numpy as np
import re


def display_events_and_line(
        resolution: tuple,
        events: np.ndarray,
        line_parameters: tuple,
        display_image: bool = False,
        save_image: bool = False,
        image_path: str = None,
) -> None:
    fig = plt.figure(figsize=(resolution[0] / 100, resolution[1] / 100))
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
        path, _ = os.path.split(image_path)
        utils.handle_path(path)

        plt.savefig(image_path)

    if display_image:
        plt.show()

    plt.close(fig)


def plot_angle_evolution(csv_angles_file: str) -> None:
    angles_data = pd.read_csv(csv_angles_file, header=None, names=['key', 'value'])

    fig = plt.figure(figsize=(10, 5))
    plt.plot(np.array(angles_data['key']), np.array(angles_data['value']), linestyle='-', color='blue')
    plt.xlabel('Time steps')
    plt.ylabel('Angle (degrees)')
    plt.title('Evolution of the detected angles')
    plt.grid(True)
    plt.savefig('angles_evolution.png')
    plt.show()
    plt.close(fig)


def create_gif_from(source_images_path: str, animation_path: str) -> None:
    path, _ = os.path.split(source_images_path)
    utils.handle_path(path)

    file_names = sorted(os.listdir(source_images_path),
                        key=lambda x: int(re.findall(r'\d+', x)[0]) if re.findall(r'\d+', x) else float('inf'))

    images = [Image.open(os.path.join(source_images_path, f)) for f in file_names if f.endswith('.png')]

    if images:
        images[0].save(animation_path, save_all=True, append_images=images[1:], loop=1)


if __name__ == '__main__':
    data = utils.load_data_from('dataset/dvSave-2024_11_26_11_34_19.aedat4')
    source_resolution = utils.event_stream_resolution(data)
    source_events = utils.get_events_from(data)

    detected_angles = {}
    slices = utils.slice_every_events(source_events, 800)

    for i, s in enumerate(slices):
        angle, line_params = utils.detect_line_angle(source_resolution, s)
        detected_angles[i] = angle
        display_events_and_line(
            source_resolution,
            s,
            line_params,
            save_image=True,
            image_path=f'images_dvSave-2024_11_26_11_34_19/image_slice_{i}.png'
        )

    utils.save_dict_to_csv(detected_angles, './detected_angles_dvSave-2024_11_26_11_34_19.csv')

    plot_angle_evolution('./detected_angles_dvSave-2024_11_26_11_34_19.csv')

    create_gif_from(
        './images_dvSave-2024_11_26_11_34_19',
        './images_dvSave-2024_11_26_11_34_19/reference_dvSave-2024_11_26_11_34_19.gif'
    )
