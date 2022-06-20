import logging
import math
import os
from typing import Tuple

import face_recognition
from PIL import Image, ImageDraw, ImageOps


class EyelignImage:
    def __init__(
        self,
        filepath,
        filename,
        find_eyes_attempted=False,
        lx=None,
        ly=None,
        rx=None,
        ry=None,
    ):
        self.filepath = filepath
        self.filename = filename
        self.find_eyes_attempted = find_eyes_attempted
        self.rx = rx
        self.ry = ry
        self.lx = lx
        self.ly = ly

    @property
    def eyes_found(self):
        return (
            self.lx is not None
            and self.ly is not None
            and self.rx is not None
            and self.ry is not None
        )

    def find_eyes(self):
        """Locate the eye positions in the image. Populates lx, ly, rx & ry."""
        image = face_recognition.load_image_file(
            os.path.join(self.filepath, self.filename)
        )
        facial_landmarks = face_recognition.face_landmarks(image)
        num_faces = len(facial_landmarks)
        if num_faces < 1:
            logging.warning(f"Cannot find face in '{self.filename}'.")
        elif num_faces > 1:
            logging.warning(f"Multiple faces found in '{self.filename}'.")
        else:
            left_eye = self._centroid(facial_landmarks[0]["left_eye"])
            self.lx = left_eye[0]
            self.ly = left_eye[1]
            right_eye = self._centroid(facial_landmarks[0]["right_eye"])
            self.rx = right_eye[0]
            self.ry = right_eye[1]
            logging.info(f"Successfully located eyes in '{self.filename}'.")
        self.find_eyes_attempted = True

    def transform(
        self,
        output_image_size: Tuple,
        eye_width_pct: int,
        output_path: str,
        debug: bool = False,
    ) -> None:
        """Transform the image to align with others based on the specified
        configuration."""
        if not self.eyes_found:
            raise ValueError(
                "Images without eye positions cannot be transformed!"
            )

        image = Image.open(os.path.join(self.filepath, self.filename))
        image = ImageOps.exif_transpose(image)  # Honour EXIF orientation tag

        if debug:
            draw = ImageDraw.Draw(image)
            radius = int(self._x_distance * 0.08)
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
            image = self._add_safety_border(
                image
            )  # Add a border to ensure no image data is lost in the rotation.
            rotation_deg = self._rotation_required()
            image = image.rotate(
                rotation_deg, center=(self.lx, self.ly), resample=Image.BICUBIC
            )
            self.rx, self.ry = self._calc_r_after_rotation(
                self.lx, self.ly, self.rx, self.ry, rotation_deg
            )

            # Normalise Eye Distance
            resize_factor = (
                output_image_size[0] * (eye_width_pct / 100)
            ) / self._x_distance
            image = image.resize(
                (
                    int(image.width * resize_factor),
                    int(image.height * resize_factor),
                )
            )
            for position in ["lx", "ly", "rx", "ry"]:
                setattr(
                    self, position, getattr(self, position) * resize_factor
                )

            # Final Crop
            x_to_edge = int(output_image_size[0] / 2)
            y_to_edge = int(output_image_size[1] / 2)
            image = image.crop(
                (
                    self._eye_center[0] - x_to_edge,
                    self._eye_center[1] - y_to_edge,
                    self._eye_center[0] + x_to_edge,
                    self._eye_center[1] + y_to_edge,
                )
            )

        image.save(os.path.join(output_path, self.filename))
        image.close()
        logging.info(f"Transformed image '{self.filename}'.")

    def _centroid(self, polygon):
        """Find the center point of a given polygon."""
        num_points = len(polygon)
        x = [point[0] for point in polygon]
        y = [point[1] for point in polygon]
        return (int(sum(x) / num_points), int(sum(y) / num_points))

    @property
    def _x_distance(self):
        """The distance between eyes on the x axis."""
        return self.rx - self.lx

    @property
    def _y_distance(self):
        """The distance between eyes on the y axis."""
        return self.ry - self.ly

    @property
    def _eye_center(self):
        """A tuple respresenting the center point between the eyes."""
        return (
            int(self.lx + (self._x_distance / 2)),
            int(self.ly + (self._y_distance / 2)),
        )

    def _rotation_required(self):
        """Return the rotaion required (in degrees) in order to straighten the
        eyes."""
        return (
            abs(math.degrees(math.atan2(self.lx - self.rx, self.ly - self.ry)))
            - 90
        )

    def _add_safety_border(self, image):
        """Add a border around the image that will prevent loss for any
        rotation."""
        max_dist = int(math.hypot(image.width, image.height))
        image = ImageOps.expand(image, max_dist)
        for position in ["lx", "ly", "rx", "ry"]:
            setattr(self, position, getattr(self, position) + max_dist)
        return image

    @classmethod
    def _calc_r_after_rotation(cls, lx, ly, rx, ry, rotation_deg):
        """Return the position of 'r' as a tuple after rotating the image by
        'rotation_deg' around 'l'."""
        y = ry - ly
        x = rx - lx
        a = math.radians(rotation_deg)

        new_ry = y * math.cos(a) - x * math.sin(a)
        new_rx = y * math.sin(a) + x * math.cos(a)
        return (int(new_rx + lx), int(new_ry + ly))
