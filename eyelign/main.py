import logging

import click

from eyelign import Eyelign

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s]: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


@click.command()
@click.option("--width", prompt="Output Image Width", type=click.INT)
@click.option("--height", prompt="Output Image Height", type=click.INT)
@click.option("--eye-width-pct", default=20, type=click.INT)
@click.option("--ignore-missing", default=False, type=click.BOOL)
def cli(width, height, eye_width_pct, ignore_missing):
    eyelign = Eyelign("/input", "/output", (width, height), eye_width_pct)
    eyelign.process_images(ignore_missing=ignore_missing)


if __name__ == "__main__":
    cli()
