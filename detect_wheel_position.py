import os
import argparse
from PIL import Image
import matplotlib.pyplot as plt
import pandas as pd
import utils
import numpy as np
import re
from tqdm import tqdm


def display_events_and_line(
        resolution: tuple,
        events: np.ndarray,
        line_parameters: tuple,
        display_image: bool = False,
        save_image: bool = False,
        image_path: str = None,
) -> None:
    """
    Presents a Matplotlib figure showing the line corresponding with the given parameters (red line) into the given set of events (blue dots).
    :param resolution: width and height of the figure
    :param events: The events to be displayed
    :param line_parameters: Rho and theta parameters of the line.
    :param display_image: If the image should be displayed
    :param save_image: If the image should be saved
    :param image_path: Where the image should be saved
    :return: None
    """
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
    """
    Plots the angle evolution given in csv file.
    :param csv_angles_file: A CSV file containing the slice number and the angle detect on each slice.
    :return: None
    """
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
    """
    Create an animated gif from a set of png files.
    :param source_images_path: The path to a directory containing the png files.
    :param animation_path: The path to a directory where the animation should be saved.
    :return: None
    """
    path, _ = os.path.split(source_images_path)
    utils.handle_path(path)

    file_names = sorted(os.listdir(source_images_path),
                        key=lambda x: int(re.findall(r'\d+', x)[0]) if re.findall(r'\d+', x) else float('inf'))

    images = [Image.open(os.path.join(source_images_path, f)) for f in file_names if f.endswith('.png')]

    if images:
        images[0].save(animation_path, save_all=True, append_images=images[1:], loop=1)


def str2bool(v: bool | str) -> bool:
    """
    Converts a string to bool.
    :param v: A string equivalent to a bool value.
    :return: The corresponding bool value.
    """
    if isinstance(v, bool):
        return v
    if v.lower() in ('true','t', '1'):
        return True
    elif v.lower() in ('false', 'f', '0'):
        return False


def get_execution_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Detect wheel position in a event dataset.',
    )
    parser.add_argument(
        'aedat4',
        type=str,
        help='Path to the AEDAT4 file'
    )
    parser.add_argument(
        '-e', '--events-per-slice',
        type=int,
        default=800,
        help='Number of events per slice'
    )
    parser.add_argument(
        '-r', '--rho',
        type=int,
        default=1,
        help='Rho parameter of the HoughLines algorithm'
    )
    parser.add_argument(
        '-t', '--theta',
        type=float,
        default=np.pi / 180,
        help='Theta parameter of the HoughLines algorithm'
    )
    parser.add_argument(
        '-th', '--threshold',
        type=int,
        default=10,
        help='Threshold for detection'
    )
    parser.add_argument(
        '-d', '--detect-wheel-position',
        type=str2bool,
        default=True,
        help='Generate a directory containing one png image per processed slice and a csv file containing '
             'the angle of the detected line in each slice'
    )
    parser.add_argument(
        '-a', '--plot-angle-evolution',
        type=str2bool,
        default=False,
        help='Plot and save the angle evolution.'
    )
    parser.add_argument(
        '-g', '--generate-gif',
        type=str2bool,
        default=False,
        help='Generate a GIF animation.'
    )

    return parser.parse_args()


if __name__ == '__main__':
    args = get_execution_arguments()
    _, file_name = os.path.split(args.aedat4)
    data = utils.load_data_from(args.aedat4)
    source_resolution = utils.event_stream_resolution(data)
    source_events = utils.get_events_from(data)
    slices = utils.slice_every_events(source_events, args.events_per_slice)

    if args.detect_wheel_position:
        detected_angles = {}

        for i, s in tqdm(enumerate(slices), total=len(slices), desc='Processing slices', ncols=80, leave=False, colour='red'):
            angle, line_params = utils.detect_line_angle(source_resolution, s, args.rho, args.theta, args.threshold)
            detected_angles[i] = angle
            display_events_and_line(
                source_resolution,
                s,
                line_params,
                save_image=True,
                image_path=f"images_{file_name.split('.')[0]}/image_slice_{i}.png"
            )

        utils.save_dict_to_csv(detected_angles, f"./detected_angles_{file_name.split('.')[0]}.csv")

    if args.plot_angle_evolution:
        plot_angle_evolution(f"./detected_angles_{file_name.split('.')[0]}.csv")

    if args.generate_gif:
        create_gif_from(
            f"./images_{file_name.split('.')[0]}",
            f"./images_{file_name.split('.')[0]}/reference_{file_name.split('.')[0]}.gif"
        )
