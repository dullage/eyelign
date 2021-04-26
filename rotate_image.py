import json
import math
import os
from typing import Tuple

from PIL import Image


class Eyelign:
    DB_FILENAME = ".eyelign"
    SUPPORTED_INPUT_EXTENSIONS = ("jpg", "jpeg")

    def __init__(
        self,
        input_path,
        output_path,
        output_image_size,
        output_eye_width_pct,
    ):
        self.input_path = input_path
        self.output_path = output_path
        self.output_image_size = output_image_size
        self.output_eye_width_pct = output_eye_width_pct

        # if len(os.listdir(output_path)) != 0:
        #     raise ValueError("Output directory must be empty!")

        self.cache = self.load_cache()
        self.images = self.populate_images()

    @property
    def db_path(self):
        return os.path.join(self.input_path, self.DB_FILENAME)

    def load_cache(self):
        try:
            with open(self.db_path, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def get_input_filenames(self):
        return [
            fn
            for fn in os.listdir(self.input_path)
            if os.path.isfile(os.path.join(self.input_path, fn))
            and fn.endswith(self.SUPPORTED_INPUT_EXTENSIONS)
        ]

    def populate_images(self):
        images = []
        for filename in self.get_input_filenames():
            try:
                cached_data = self.cache[filename]
                images.append(
                    EyelignImage(
                        self.input_path,
                        filename,
                        cached_data["lx"],
                        cached_data["ly"],
                        cached_data["rx"],
                        cached_data["ry"],
                    )
                )
            except KeyError:
                pass  # TODO: Find eye positions
        return images

    def go(self):
        for image in self.images:
            image.align(
                self.output_image_size,
                self.output_eye_width_pct,
                self.output_path,
            )


class EyelignImage:
    def __init__(self, filepath, filename, lx, ly, rx, ry):
        self.filepath = filepath
        self.filename = filename
        self.rx = rx
        self.ry = ry
        self.lx = lx
        self.ly = ly

    @property
    def x_distance(self):
        """The distance between eyes on the x axis."""
        return self.rx - self.lx

    @property
    def y_distance(self):
        """The distance between eyes on the y axis."""
        return self.ry - self.ly

    @property
    def eye_center(self):
        """A tuple respresenting the center point between the eyes."""
        return (
            int(self.lx + (self.x_distance / 2)),
            int(self.ly + (self.y_distance / 2)),
        )

    def rotation_required(self):
        """Return the rotaion required (in degrees) in order to straighten the eyes."""
        return (
            abs(math.degrees(math.atan2(self.lx - self.rx, self.ly - self.ry)))
            - 90
        )

    @classmethod
    def calc_r_after_rotation(self, lx, ly, rx, ry, rotation_deg):
        """Return the position of 'r' as a tuple after rotating the image by 'rotation_deg' around 'l'."""
        y = ry - ly
        x = rx - lx
        a = math.radians(rotation_deg)

        new_ry = y * math.cos(a) - x * math.sin(a)
        new_rx = y * math.sin(a) + x * math.cos(a)
        return (int(new_rx + lx), int(new_ry + ly))

    def align(
        self, output_image_size: Tuple, eye_width_pct: int, output_path: str
    ) -> None:
        image = Image.open(os.path.join(self.filepath, self.filename))

        # Straighten Eyes
        rotation_deg = self.rotation_required()
        image = image.rotate(
            rotation_deg, center=(self.lx, self.ly), resample=Image.BICUBIC
        )
        self.rx, self.ry = self.calc_r_after_rotation(
            self.lx, self.ly, self.rx, self.ry, rotation_deg
        )

        # Normalise Eye Distance
        resize_factor = (
            output_image_size[0] * (eye_width_pct / 100)
        ) / self.x_distance
        image = image.resize(
            (
                int(image.width * resize_factor),
                int(image.height * resize_factor),
            )
        )
        self.lx = int(self.lx * resize_factor)
        self.ly = int(self.ly * resize_factor)
        self.rx = int(self.rx * resize_factor)
        self.ry = int(self.ry * resize_factor)

        # Final Crop
        x_to_edge = int(output_image_size[0] / 2)
        y_to_edge = int(output_image_size[1] / 2)
        image = image.crop(
            (
                self.eye_center[0] - x_to_edge,
                self.eye_center[1] - y_to_edge,
                self.eye_center[0] + x_to_edge,
                self.eye_center[1] + y_to_edge,
            )
        )

        image.save(os.path.join(output_path, self.filename))
        image.close()


if __name__ == "__main__":
    eyelign = Eyelign("input", "output", (400, 600), 25)
    eyelign.go()
