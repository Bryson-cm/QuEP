"""Build an MP4 movie from frame images in an animation directory."""

import os
import time
from pathlib import Path

import cv2


def _find_images(image_folder):
    """Return sorted PNG/JPG/JPEG files from image_folder."""
    exts = {".png", ".jpg", ".jpeg"}
    return sorted(
        p for p in Path(image_folder).iterdir()
        if p.is_file() and p.suffix.lower() in exts
    )


def _make_writer(video_path, fps, frame_size):
    """Create a VideoWriter, trying common MP4 codecs in order."""
    for codec in ("avc1", "mp4v", "H264", "XVID"):
        fourcc = cv2.VideoWriter_fourcc(*codec)
        writer = cv2.VideoWriter(str(video_path), fourcc, fps, frame_size)
        if writer.isOpened():
            print(f"Using video codec: {codec}")
            return writer
        writer.release()
    raise RuntimeError("Could not create an OpenCV VideoWriter. Try installing ffmpeg/OpenCV with MP4 codec support.")


def generatemovie(fps, new_path, dim_scale=1.0):
    """Generate an MP4 movie from PNG/JPG frames in new_path.

    Parameters
    ----------
    fps : int or float
        Frames per second for the output movie.
    new_path : str or path-like
        Folder containing frame images.
    dim_scale : float, optional
        Resize scale relative to the first frame. Default is 1.0.

    Returns
    -------
    str
        Full path to the generated movie.
    """
    image_folder = Path(new_path).expanduser().resolve()
    if not image_folder.is_dir():
        raise FileNotFoundError(f"Frame folder does not exist: {image_folder}")
    if fps <= 0:
        raise ValueError("fps must be greater than zero.")
    if dim_scale <= 0:
        raise ValueError("dim_scale must be greater than zero.")

    images = _find_images(image_folder)
    if not images:
        raise FileNotFoundError(f"No .png, .jpg, or .jpeg frames found in: {image_folder}")

    first = cv2.imread(str(images[0]))
    if first is None:
        raise RuntimeError(f"Could not read first frame: {images[0]}")

    old_height, old_width = first.shape[:2]
    new_width = int(old_width * dim_scale)
    new_height = int(old_height * dim_scale)
    frame_size = (new_width, new_height)

    print(f"New dimensions for video: {new_width}x{new_height}px")
    print(f"Running at {fps} frames per second")
    print(f"Using {len(images)} images from: {image_folder}")

    dim_scale_label = f"{dim_scale:03.2f}".replace(".", "-")
    video_path = image_folder / f"00-progression-movie__{dim_scale_label}res__{fps}fps.mp4"

    video = _make_writer(video_path, fps, frame_size)

    start_time_video = time.time()
    print("\nMovie generation - START TIME:", time.strftime("%H:%M:%S", time.localtime()))

    try:
        for image in images:
            img = cv2.imread(str(image))
            if img is None:
                print(f"Skipping unreadable frame: {image}")
                continue
            frame = cv2.resize(img, dsize=frame_size, interpolation=cv2.INTER_CUBIC)
            video.write(frame)
    finally:
        video.release()
        cv2.destroyAllWindows()

    print(f"Movie generated! File stored at {video_path}")
    print("Movie generation - END TIME:", time.strftime("%H:%M:%S", time.localtime()))
    print("Movie generation - DURATION:", (time.time() - start_time_video) / 60, "min\n")

    return str(video_path)
