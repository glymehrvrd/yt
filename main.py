import yt_dlp
import json
import time
import sys
from dao import DAO
from yt_dlp_plugins.postprocessor.transcriber import TranscriberPP


# Define constant for Odd Lots playlist ID
ODD_LOTS_PLAYLIST_ID = "PLe4PRejZgr0MuA6M0zkZyy-99-qc87wKV"


def find_all_videos_in_playlist(playlist_id: str):
    yt_obs: dict[str, bool | str] = {
        "quiet": True,
        "skip_download": True,
        "noplaylist": True,
        "extract_flat": "in_playlist",
        "sort": "date",
        "restrictfilenames": True,
        "extractor_args": {"youtubetab": {"approximate_date": [""]}},
    }

    # Extract playlist info
    playlist_info = yt_dlp.YoutubeDL(yt_obs).extract_info(f"https://www.youtube.com/playlist?list={playlist_id}")

    # Extract video information from the playlist
    videos = []
    if "entries" in playlist_info:
        for entry in playlist_info["entries"]:
            if entry and entry.get("title") != "[Private video]":
                video = {
                    "title": entry.get("title"),
                    "url": entry.get("url"),
                    "id": entry.get("id"),
                    "timestamp": entry.get("timestamp"),
                }
                videos.append(video)
    return videos


def download_video(vid: str) -> None:
    ydl_opts = {
        # "quiet": True,
        "format": "bestaudio/best",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            },
            {
                "key": "Transcriber",
            },
        ],
        "outtmpl": "downloads/%(title)s.%(ext)s",
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            ydl.extract_info(f"https://www.youtube.com/watch?v={vid}", download=True)
        except Exception as e:
            print(f"Error downloading video {vid}: {str(e)}")


def get_new_videos(playlist_id, dao):
    videos = find_all_videos_in_playlist(playlist_id)
    if len(videos) == 0:
        print("No videos found in the playlist.")
        return []

    last_id = dao.get_last_downloaded_id(playlist_id)
    if last_id is None:
        last_id = "98PAA8q619I"
    print(f"last_downloaded_id: {last_id}")

    last_index = next((i for i, video in enumerate(videos) if video["id"] == last_id), None)

    if last_index is None:
        print(f"Video with ID {last_id} not found in the playlist.")
        new_videos = videos
    else:
        new_videos = videos[:last_index]

    return new_videos[::-1]


def download_with_retry(video, max_retries=3) -> None:
    for retry_count in range(max_retries):
        if retry_count > 0:
            print(f"Retrying download of video {video['id']} (Attempt {retry_count + 1}/{max_retries})")

        try:
            download_video(video["id"])
            return
        except Exception as e:
            print(f"Error downloading video {video['id']}: {str(e)}")
            if retry_count < max_retries - 1:
                wait_time = 2 ** (retry_count + 1)  # Exponential backoff
                print(f"Waiting {wait_time} seconds before next attempt...")
                time.sleep(wait_time)

    error_message = f"Failed to download video {video['id']} after {max_retries} attempts"
    print(error_message)
    raise Exception(error_message)


def main():
    dao = DAO()
    new_videos = get_new_videos(ODD_LOTS_PLAYLIST_ID, dao)
    print(f"Found {len(new_videos)} new videos to download.")

    for video in new_videos:
        print(f"Downloading video: {video['id']} - {video['title']}")
        download_with_retry(video)
        dao.update_last_downloaded_id(ODD_LOTS_PLAYLIST_ID, video["id"])


if __name__ == "__main__":
    main()
