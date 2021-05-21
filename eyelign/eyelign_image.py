import logging
import math
import os
from typing import Tuple

from PIL import Image, ImageDraw, ImageOps


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

    def _rotation_required(self):
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

    def process(
        self,
        output_image_size: Tuple,
        eye_width_pct: int,
        output_path: str,
        debug: bool = False,
    ) -> None:
        image = Image.open(os.path.join(self.filepath, self.filename))
        image = ImageOps.exif_transpose(image)  # Honour EXIF orientation tag

        if debug:
            draw = ImageDraw.Draw(image)
            radius = int(self.x_distance * 0.08)
            eyes = ((self.lx, self.ly), (self.rx, self.ry))
            for eye in eyes:
                draw.ellipse(
                    [
                        (eye[0] - radius, eye[1] - radius),
                        (eye[0] + radius, eye[1] + radius),
                    ],
                    fill=(200, 0, 0),
                )

        else:
            # Straighten Eyes
            rotation_deg = self._rotation_required()
            image = image.rotate(
                rotation_deg, center=(self.lx, self.ly), resample=Image.BICUBIC
            )  # TODO: Add border to ensure no image data is lost in the rotation.
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
        logging.info(f"Processed image '{self.filename}'")
