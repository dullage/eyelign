import json
import logging
import os

import face_recognition
from eyelign_image import EyelignImage


class Eyelign:
    CACHE_FILENAME = ".eyelign"
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

        self.load_cache()
        self.missing_eye_positions = 0
        self.images = self.populate_images()

    @property
    def cache_path(self):
        return os.path.join(self.input_path, self.CACHE_FILENAME)

    def load_cache(self):
        try:
            with open(self.cache_path, "r") as f:
                self.cache = json.load(f)
        except FileNotFoundError:
            self.cache = {}

    def save_cache(self):
        with open(self.cache_path, "w") as f:
            json.dump(self.cache, f, indent=2)

    def get_input_filenames(self):
        return [
            fn
            for fn in os.listdir(self.input_path)
            if os.path.isfile(os.path.join(self.input_path, fn))
            and fn.lower().endswith(self.SUPPORTED_INPUT_EXTENSIONS)
        ]

    def centroid(self, polygon):
        num_points = len(polygon)
        x = [point[0] for point in polygon]
        y = [point[1] for point in polygon]
        return (int(sum(x) / num_points), int(sum(y) / num_points))

    def find_eyes(self, filename):
        image = face_recognition.load_image_file(
            os.path.join(self.input_path, filename)
        )
        facial_landmarks = face_recognition.face_landmarks(image)
        num_faces = len(facial_landmarks)

        if num_faces < 1:
            logging.warning(f"Cannot find face in '{filename}'.")
            lx = ly = rx = ry = None
        elif num_faces > 1:
            logging.warning(f"Multiple faces found in '{filename}'.")
            lx = ly = rx = ry = None
        else:
            left_eye = self.centroid(facial_landmarks[0]["left_eye"])
            lx = left_eye[0]
            ly = left_eye[1]
            right_eye = self.centroid(facial_landmarks[0]["right_eye"])
            rx = right_eye[0]
            ry = right_eye[1]
            logging.info(f"Successfully located eyes in '{filename}'.")

        return {
            "lx": lx,
            "ly": ly,
            "rx": rx,
            "ry": ry,
        }

    def populate_images(self):
        images = []
        for filename in self.get_input_filenames():
            try:
                eye_positions = self.cache[filename]
            except KeyError:
                eye_positions = self.find_eyes(filename)
                self.cache[filename] = eye_positions
                self.save_cache()

            missing_eye_positions = len(
                [
                    position
                    for position in eye_positions.values()
                    if position is None
                ]
            )

            if missing_eye_positions > 0:
                logging.warning(f"Eye positions missing for {filename}.")
                self.missing_eye_positions += 1
            else:
                images.append(
                    EyelignImage(
                        self.input_path,
                        filename,
                        eye_positions["lx"],
                        eye_positions["ly"],
                        eye_positions["rx"],
                        eye_positions["ry"],
                    )
                )
        return images

    def process_images(self, ignore_missing=False, debug=False):
        if len(os.listdir(self.output_path)) != 0:
            logging.error("Output directory must be empty!")
            return

        if ignore_missing is False and self.missing_eye_positions > 0:
            logging.error(
                f"{self.missing_eye_positions} images have missing eye positions. Please manually edit the cache file or specify '--ignore-missing'."
            )
            return

        for image in self.images:
            image.process(
                self.output_image_size,
                self.output_eye_width_pct,
                self.output_path,
                debug,
            )
