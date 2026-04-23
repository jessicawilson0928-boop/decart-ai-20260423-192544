import argparse
import asyncio
import contextlib
import os
import sys
from typing import Optional

import cv2
from aiortc import MediaStreamTrack, VideoStreamTrack
from av import VideoFrame
from decart import DecartClient, models
from decart.realtime import RealtimeClient, RealtimeConnectOptions
from decart.types import ModelState, Prompt


class OpenCVCameraTrack(VideoStreamTrack):
    def __init__(self, camera_index: int, width: int, height: int, fps: int) -> None:
        super().__init__()
        backend = cv2.CAP_DSHOW if sys.platform.startswith("win") else 0
        self.cap = cv2.VideoCapture(camera_index, backend)
        if not self.cap.isOpened():
            raise RuntimeError(
                f"Could not open camera index {camera_index}. Run with --list-cameras to find valid indexes."
            )

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.cap.set(cv2.CAP_PROP_FPS, fps)
        self._stopped = False

    async def recv(self) -> VideoFrame:
        pts, time_base = await self.next_timestamp()
        ok, frame = self.cap.read()
        if not ok:
            raise RuntimeError("Failed to read frame from camera.")

        video_frame = VideoFrame.from_ndarray(frame, format="bgr24")
        video_frame.pts = pts
        video_frame.time_base = time_base
        return video_frame

    def stop(self) -> None:
        if not self._stopped:
            self.cap.release()
            self._stopped = True
        super().stop()


def list_cameras(max_index: int) -> None:
    backend = cv2.CAP_DSHOW if sys.platform.startswith("win") else 0
    found = False
    for index in range(max_index + 1):
        cap = cv2.VideoCapture(index, backend)
        if not cap.isOpened():
            continue

        ok, frame = cap.read()
        if ok and frame is not None:
            height, width = frame.shape[:2]
            print(f"camera_index={index} resolution={width}x{height}")
            found = True
        cap.release()

    if not found:
        print("No camera devices found.")


def build_initial_state(prompt_text: Optional[str], image: Optional[str], enhance: bool) -> Optional[ModelState]:
    if not prompt_text and not image:
        return None

    state = ModelState()
    if prompt_text:
        state.prompt = Prompt(text=prompt_text, enhance=enhance)
    if image:
        state.image = image
    return state


async def render_remote_stream(
    remote_track: MediaStreamTrack,
    stop_event: asyncio.Event,
    window_name: str,
) -> None:
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    try:
        while not stop_event.is_set():
            frame = await remote_track.recv()
            image = frame.to_ndarray(format="bgr24")
            cv2.imshow(window_name, image)
            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), 27):
                stop_event.set()
                break
            await asyncio.sleep(0)
    finally:
        cv2.destroyWindow(window_name)


async def run(args: argparse.Namespace) -> None:
    if args.list_cameras:
        list_cameras(args.max_camera_index)
        return

    raw_api_key = os.getenv("DECART_API_KEY")
    api_key = raw_api_key.strip() if raw_api_key else ""
    api_key = api_key.strip("{}")
    if not api_key:
        raise RuntimeError("Missing DECART_API_KEY environment variable.")

    client = DecartClient(api_key=api_key)
    model = models.realtime(args.model)
    initial_state = build_initial_state(args.prompt, args.image, not args.no_enhance)

    camera_track = OpenCVCameraTrack(
        camera_index=args.camera_index,
        width=model.width,
        height=model.height,
        fps=model.fps,
    )

    stop_event = asyncio.Event()
    render_task: Optional[asyncio.Task] = None
    realtime_error: list[Exception] = []

    def on_remote_stream(track: MediaStreamTrack) -> None:
        nonlocal render_task
        print("remote_stream=connected")
        if render_task is None or render_task.done():
            render_task = asyncio.create_task(
                render_remote_stream(track, stop_event, args.window_name)
            )

    options = RealtimeConnectOptions(
        model=model,
        on_remote_stream=on_remote_stream,
        initial_state=initial_state,
    )

    realtime = await RealtimeClient.connect(
        base_url=client.realtime_base_url,
        api_key=client.api_key,
        local_track=camera_track,
        options=options,
        integration=client.integration,
    )

    def on_connection_change(state: str) -> None:
        print(f"connection_state={state}")

    def on_error(error: Exception) -> None:
        print(f"realtime_error={error}")
        realtime_error.append(error)
        stop_event.set()

    realtime.on("connection_change", on_connection_change)
    realtime.on("error", on_error)

    print("Streaming started. Press q in the output window (or Ctrl+C in terminal) to stop.")

    try:
        while not stop_event.is_set():
            if render_task and render_task.done():
                err = render_task.exception()
                if err:
                    raise err
                stop_event.set()
                break
            if realtime_error:
                raise RuntimeError(str(realtime_error[0]))
            await asyncio.sleep(0.2)
    finally:
        stop_event.set()
        if render_task:
            with contextlib.suppress(asyncio.CancelledError):
                if not render_task.done():
                    render_task.cancel()
                await render_task
        await realtime.disconnect()
        camera_track.stop()
        cv2.destroyAllWindows()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Decart Lucy realtime transformation for live streaming."
    )
    parser.add_argument(
        "--model",
        default="lucy-latest",
        help="Realtime model ID (e.g. lucy-latest, lucy-2, lucy-2.1).",
    )
    parser.add_argument(
        "--camera-index",
        type=int,
        default=0,
        help="Camera index to capture from.",
    )
    parser.add_argument(
        "--prompt",
        default="Enhance this live video for a polished cinematic stream look.",
        help="Prompt applied to the live stream.",
    )
    parser.add_argument(
        "--image",
        default=None,
        help="Optional reference image path or URL for character transformation.",
    )
    parser.add_argument(
        "--no-enhance",
        action="store_true",
        help="Disable prompt enhancement.",
    )
    parser.add_argument(
        "--window-name",
        default="Decart Lucy Realtime Output",
        help="Window title used for displaying transformed stream.",
    )
    parser.add_argument(
        "--list-cameras",
        action="store_true",
        help="List available camera indexes and exit.",
    )
    parser.add_argument(
        "--max-camera-index",
        type=int,
        default=10,
        help="Highest camera index to probe when using --list-cameras.",
    )
    return parser.parse_args()


if __name__ == "__main__":

    arguments = parse_args()
    try:
        asyncio.run(run(arguments))
    except KeyboardInterrupt:
        print("Stopped.")
