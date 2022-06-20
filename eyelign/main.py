import logging

import click

from eyelign import Eyelign

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s]: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


@click.command()
@click.argument(
    "input_dir",
    type=click.Path(exists=True, readable=True),
    envvar="EYELIGN_INPUT_DIR",
)
@click.argument(
    "output_dir",
    type=click.Path(exists=True, writable=True),
    envvar="EYELIGN_OUTPUT_DIR",
)
@click.option(
    "--find-eyes",
    default=True,
    type=click.BOOL,
    show_default=True,
    help="Find eyes in new images.",
)
@click.option(
    "--transform-images",
    default=True,
    type=click.BOOL,
    show_default=True,
    help="Transform images and save output in OUTPUT_DIR.",
)
@click.option(
    "--output-width", prompt="Output Image Width", type=click.INT, help=""
)
@click.option("--output-height", prompt="Output Image Height", type=click.INT)
@click.option(
    "--eye-width-pct",
    default=20,
    type=click.INT,
    show_default=True,
    help="Determines the width of the eyes as a percentage of the output "
    "width.",
)
@click.option(
    "--ignore-missing",
    default=False,
    type=click.BOOL,
    help="Output will normally fail if any images are missing eye positions. "
    "Set this to true to override normal behaviour.",
)
@click.option(
    "--debug",
    default=False,
    type=click.BOOL,
    help="Skips all image transformation and simply outputs copies of the "
    "source images with eye positions highlighted. Useful to check eye "
    "positions are correct.",
)
def cli(
    input_dir,
    output_dir,
    find_eyes,
    transform_images,
    ignore_missing,
    output_width,
    output_height,
    eye_width_pct,
    debug,
):
    eyelign = Eyelign(
        input_dir, output_dir, (output_width, output_height), eye_width_pct
    )
    if find_eyes:
        eyelign.find_eyes()
    if transform_images:
        eyelign.transform_images(ignore_missing=ignore_missing, debug=debug)


if __name__ == "__main__":
    cli()
