# eyelign

A tool to align multiple portrait photos by eye position. Eye posiitons are automatically found using the Python package [face_recognition](https://github.com/ageitgey/face_recognition).

## Instructions

First clone this repo:

```bash
git clone https://github.com/Dullage/eyelign.git
```

Next, build the Docker image:

```bash
docker build -t dullage/eyelign:latest /path/to/cloned/repo
```

Ensure all of your images are a single flat directory. This will be the `input` folder.

Create an empty folder for the aligned images. This will be the `output` folder.

Run the Docker image with the 2 folders as volume mounts:

```bash
docker run -it --rm \
  -v "/input/folder/path:/input" \
  -v "/output/folder/path:/output" \
  dullage/eyelign:latest
```

You will be promted to enter a desired width and height for the output images. Equally you can specify these in the docker run command:

```bash
docker run -it --rm \
  -v "/input/folder/path:/input" \
  -v "/output/folder/path:/output" \
  dullage/eyelign:latest \
  --width 600 \
  --height 800
```

All eye positions are cached in the input folder in a file called `.eyelign`. This negates the need to find them again on following runs.
