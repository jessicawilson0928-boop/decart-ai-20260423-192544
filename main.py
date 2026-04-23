import argparse
import asyncio
import os

from decart import DecartClient, models


async def run_video_job(prompt: str, video_url: str, output_path: str) -> None:
    api_key = os.getenv("DECART_API_KEY")
    if not api_key:
        raise RuntimeError("Missing DECART_API_KEY environment variable.")

    async with DecartClient(api_key=api_key) as client:
        result = await client.queue.submit_and_poll(
            {
                "model": models.video("lucy-2"),
                "data": video_url,
                "prompt": prompt,
                "on_status_change": lambda job: print(f"status={job.status}"),
            }
        )

        if result.status != "completed":
            raise RuntimeError(f"Job did not complete successfully: {result.status}")

        data = result.data
        if isinstance(data, (bytes, bytearray, memoryview)):
            content = bytes(data)
        elif hasattr(data, "read"):
            read_result = data.read()
            if asyncio.iscoroutine(read_result):
                content = await read_result
            else:
                content = read_result
        else:
            raise RuntimeError(f"Unsupported result data type: {type(data)!r}")
        with open(output_path, "wb") as output_file:
            output_file.write(content)

        print(f"Saved output to {output_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a Decart video transform job.")
    parser.add_argument(
        "--prompt",
        default="Transform this video into an anime style.",
        help="Text prompt for the transformation.",
    )
    parser.add_argument(
        "--video-url",
        required=True,
        help="Public URL to an input video file.",
    )
    parser.add_argument(
        "--output",
        default="output.mp4",
        help="Where to save the transformed video.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(run_video_job(args.prompt, args.video_url, args.output))
