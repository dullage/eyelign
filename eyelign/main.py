import logging

import click

from eyelign import Eyelign

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s]: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


@click.command()
@click.option(
    "--output-width", prompt="Output Image Width", type=click.INT, help=""
)
@click.option("--output-height", prompt="Output Image Height", type=click.INT)
@click.option(
    "--eye-width-pct",
    default=20,
    type=click.INT,
    show_default=True,
    help="Determines the width of the eyes as a percentage of the output width.",
)
@click.option(
    "--ignore-missing",
    default=False,
    type=click.BOOL,
    help="Output will normally fail if any images are missing eye positions. Set this to true to override normal behaviour.",
)
@click.option(
    "--input-only",
    default=False,
    type=click.BOOL,
    help="Only add eye positions to the .eyelign cache file. Output disabled.",
)
@click.option(
    "--debug",
    default=False,
    type=click.BOOL,
    help="Skips all image transformation and simply outputs copies of the source images with eye positions highlighted. Useful to check eye positions are correct.",
)
def cli(
    output_width,
    output_height,
    eye_width_pct,
    ignore_missing,
    input_only,
    debug,
):
    eyelign = Eyelign(
        "/input", "/output", (output_width, output_height), eye_width_pct
    )
    if not input_only:
        eyelign.process_images(ignore_missing=ignore_missing, debug=debug)


if __name__ == "__main__":
    cli()
