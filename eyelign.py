import os

import click

# from marshmallow import Schema, fields, validate

from find_eyes import find_eyes
from rotate_image import rotate_image

# class ImageFileSchema(Schema):
#     filename = fields.Str(required=True)
#     left_eye_position = fields.Tuple(
#         fields.Int(), validate=validate.Length(min=2, max=2)
#     )
#     right_eye_position = fields.Tuple(
#         fields.Int(), validate=validate.Length(min=2, max=2)
#     )


# class ImageFile:
#     def __init__(self, filename):
#         self.filename = filename


@click.command()
def cli():
    input_path = "./input"
    output_path = "./staging"
    images = [
        f
        for f in os.listdir(input_path)
        if os.path.isfile(os.path.join(input_path, f))
    ]
    for image in images:
        try:
            left_eye, right_eye = find_eyes(os.path.join(input_path, image))
            rotate_image(input_path, image, left_eye, right_eye, output_path)
        except Exception:
            print(f"No faces for: {image}")


if __name__ == "__main__":
    cli()
