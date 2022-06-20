import json
import logging
import os

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

        self.images = self._get_images()
        self._load_cache()
        self._save_cache()

    def find_eyes(self) -> None:
        for image in [
            image for image in self.images if image.eyes_found is False
        ]:
            if image.find_eyes_attempted is False:
                image.find_eyes()
                self._save_cache()
            else:
                logging.info(
                    f"Skipping '{image.filename}' as previously attempted."
                )

    def transform_images(
        self, ignore_missing: bool = False, debug: bool = False
    ) -> None:
        if len(os.listdir(self.output_path)) != 0:
            logging.error("Output directory must be empty!")
            return

        if ignore_missing is False and self._num_eyes_not_found > 0:
            logging.error(
                f"{self._num_eyes_not_found} images have missing eye"
                "positions. Please manually edit the cache file or "
                "specify '--ignore-missing'."
            )
            return

        for image in self.images:
            image.transform(
                self.output_image_size,
                self.output_eye_width_pct,
                self.output_path,
                debug,
            )

    @property
    def _cache_path(self):
        return os.path.join(self.input_path, self.CACHE_FILENAME)

    @property
    def _num_eyes_not_found(self):
        return len(
            [image for image in self.images if image.eyes_found is False]
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
                logging.info(f"'{image.filename}' loaded from cache.")
            except KeyError:
                pass

    def _save_cache(self):
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
