# eyelign

A tool to align multiple portrait photos by eye position.

## Introduction

When my daughter was born I decided to take a portrait photo of her every week with the idea of creating a timelapse when she is older.

I started out using an iOS app tailored for this purpose but I didn't like being locked into the app and the backup options were limited.

I then switched to simply using _any_ app or camera to take the photos and set out to find something that could create the timelapse. There were a few considerations:

- **I was looking for an open-source solution.** This is to avoid another app lock-in.
- **The source images would be varied in size and aspect ratio.**
- **I wanted the eyes to be aligned in each frame.** This type of timelapse is much more pleasant to watch when the eyes are aligned.
- **The position of my daughter's eyes would vary between photos.** As I write this she's 3 and it's hard enough to keep her still for 5 seconds let alone get the photo perfectly aligned!
- **The rotation of my daughter's face would vary between photos.**

At the time I couldn't find anything that fit these needs and I wanted a project so I started to piece eyelign together.

## Top-level Workflow

1. Find all jpg/jpeg files in the `INPUT_DIR`.
2. Look for a `.eyelign` file. This is used to cache eye positions so that they don't need to be found each run.
3. Loop through all of the files. For any file not in the cache, use the python package '[face_recognition](https://github.com/ageitgey/face_recognition)' to attempt to automatically find the eye positions.

Then, loop through all of the files again and for each one:

1. Rotate the image so that the eyes are level.
2. Resize the image so that in all images, the eyes are the same distance apart.
3. Crop the image to the required size using the eyes as an anchor point.
4. Save the image to the `OUTPUT_DIR`.

If the automatic eye position detection fails for any reason, the file is still added to the cache but with null values for the eye positions. This is for 2 reasons:

1. It means that eyelign won't try again the next time it is run.
2. It allows users to manually enter the eye positions. I generally do this by finding the xy values using MS Paint (visible in the bottom left corner of the app).

This example .eyelign file has 2 images saved, one with eye positions and one without:

```json
{
  "2020-01-01.jpg": {
    "find_eyes_attempted": true,
    "lx": 1194,
    "ly": 1817,
    "rx": 1651,
    "ry": 1820
  },
  "2020-01-08.jpg": {
    "find_eyes_attempted": true,
    "lx": null,
    "ly": null,
    "rx": null,
    "ry": null
  }
}
```

## Usage

The easiest way to use eyelign is to use the docker image available on Docker Hub.

```bash
docker pull dullage/eyelign:latest
```

Next, ensure all of your images are a single flat directory. This will be the `INPUT_DIR`. _Note: The images in the `INPUT_DIR` are not modified._

Create an empty folder for the aligned images. This will be the `OUTPUT_DIR`.

Run the Docker image with the 2 folders as volume mounts:

```bash
docker run -it --rm \
  -v "/input/folder/path:/input" \
  -v "/output/folder/path:/output" \
  dullage/eyelign:latest
```

That's it! After following the prompts you should have an `OUTPUT_DIR` full of aligned images. As described above, if the automatic eye position detection failed on any images you can manually edit the `.eyelign` cache file and try again.

I then use `ffpmeg` to create the timelapse from the images. I may build this into the tool some day but for now, here's an example command:

```bash
ffmpeg \
  -framerate 4 \
  -pattern_type glob \
  -i "/output/folder/path/*.jpg" \
  -s:v 810x1080 \
  -c:v libx264 \
  -crf 17 \
  -pix_fmt yuv420p \
  timelapse.mp4
```

## Options

```
  --find-eyes         BOOLEAN   Find eyes in new images.  [default: True]

  --transform-images  BOOLEAN   Transform images and save output in OUTPUT_DIR.
                                [default: True]

  --output-width      INTEGER

  --output-height     INTEGER

  --eye-width-pct     INTEGER   Determines the width of the eyes as a percentage
                                of the output width.  [default: 20]

  --ignore-missing    BOOLEAN   Output will normally fail if any images are
                                missing eye positions. Set this to true to
                                override normal behaviour.

  --workers           INTEGER   The number of CPU workers to use.  [default:
                                number of physical cores available]

  --debug             BOOLEAN   Skips all image transformation and simply
                                outputs copies of the source images with eye
                                positions highlighted. Useful to check eye
                                positions are correct.

  --help                        Show this message and exit.
```

To use an option in a Docker command simply add it to the end:

```bash
docker run -it --rm \
  -v "/input/folder/path:/input" \
  -v "/output/folder/path:/output" \
  dullage/eyelign:latest \
  --debug True
```
