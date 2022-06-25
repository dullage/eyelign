import json
import logging
import os
from multiprocessing import get_context

import psutil

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
        num_workers=None,
    ):
        self.input_path = input_path
        self.output_path = output_path
        self.output_image_size = output_image_size
        self.output_eye_width_pct = output_eye_width_pct

        self.num_workers = (
            num_workers
            if num_workers is not None
            else psutil.cpu_count(logical=False)
        )

        self.images = self._get_images()
        self._load_cache()
        self._save_cache()
        self.log_stats()

    def log_stats(self):
        logging.info(
            f"{self._num_images} images, "
            f"{self._num_images_no_eyes} missing eye positions "
            f"({self._num_images_no_eyes_attempted} already attempted)."
        )

    def find_eyes(self) -> None:
        workload = [
            image
            for image in self.images
            if image.eyes_found is False and image.find_eyes_attempted is False
        ]
        if len(workload) == 0:
            logging.info("No eyes to find (exluding those already attempted).")
            return

        logging.info(f"Finding eyes with {self.num_workers} workers.")
        with get_context("spawn").Pool(self.num_workers) as pool:
            result = pool.map(
                EyelignImage.find_eyes,
                workload,
            )

        self.images = [
            image
            for image in self.images
            if image.eyes_found is True or image.find_eyes_attempted is True
        ] + [image for image in result]

        self.log_stats()
        self._save_cache()

    def transform_images(
        self, ignore_missing: bool = False, debug: bool = False
    ) -> None:
        if len(os.listdir(self.output_path)) != 0:
            logging.error("Output directory must be empty!")
            return

        if ignore_missing is False and self._num_images_no_eyes > 0:
            logging.error(
                f"{self._num_images_no_eyes} images have missing eye"
                "positions. Please manually edit the cache file or "
                "specify '--ignore-missing'."
            )
            return

        logging.info(f"Transforming images with {self.num_workers} workers.")
        with get_context("spawn").Pool(self.num_workers) as pool:
            pool.starmap(
                EyelignImage.transform,
                [
                    (
                        image,
                        self.output_image_size,
                        self.output_eye_width_pct,
                        self.output_path,
                        debug,
                    )
                    for image in self.images
                    if image.eyes_found is True
                ],
            )

    @property
    def _cache_path(self):
        return os.path.join(self.input_path, self.CACHE_FILENAME)

    @property
    def _num_images(self):
        return len(self.images)

    @property
    def _num_images_no_eyes(self):
        return len(
            [image for image in self.images if image.eyes_found is False]
        )

    @property
    def _num_images_no_eyes_attempted(self):
        return len(
            [
                image
                for image in self.images
                if image.eyes_found is False
                and image.find_eyes_attempted is True
            ]
        )

    def _get_images(self):
        return [
            EyelignImage(self.input_path, filename)
            for filename in os.listdir(self.input_path)
            if os.path.isfile(os.path.join(self.input_path, filename))
            and filename.lower().endswith(self.SUPPORTED_INPUT_EXTENSIONS)
        ]

    def _load_cache(self):
        try:
            with open(self._cache_path, "r") as f:
                cache = json.load(f)
                logging.info("Cache loaded.")
        except FileNotFoundError:
            return

        for image in self.images:
            try:
                image.lx = cache[image.filename]["lx"]
                image.ly = cache[image.filename]["ly"]
                image.rx = cache[image.filename]["rx"]
                image.ry = cache[image.filename]["ry"]
                image.find_eyes_attempted = cache[image.filename][
                    "find_eyes_attempted"
                ]
            except KeyError:
                pass

    def _save_cache(self):
        self.images.sort(key=lambda image: image.filename)
        with open(self._cache_path, "w") as f:
            json.dump(
                {
                    image.filename: {
                        "find_eyes_attempted": image.find_eyes_attempted,
                        "lx": image.lx,
                        "ly": image.ly,
                        "rx": image.rx,
                        "ry": image.ry,
                    }
                    for image in self.images
                },
                f,
                indent=2,
            )
