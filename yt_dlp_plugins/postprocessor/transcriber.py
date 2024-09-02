import os
import datetime
from yt_dlp.postprocessor.common import PostProcessor
from faster_whisper import WhisperModel


def get_current_time():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class TranscriberPP(PostProcessor):
    def __init__(self, downloader=None, **kwargs):
        super().__init__()
        self.model = WhisperModel("small.en", device="cpu", compute_type="float32", cpu_threads=8)

    def format_timestamp(self, seconds):
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millisecs = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"

    def run(self, info):
        if not info.get("filepath"):
            self.to_screen("No file path found. Skipping transcription.")
            return [], info

        audio_path = info["filepath"]
        segments, _ = self.model.transcribe(audio_path)

        self.to_screen(f"[{get_current_time()}] Transcribing {audio_path}")

        srt_path = f"{os.path.splitext(audio_path)[0]}.srt"
        txt_path = f"{os.path.splitext(audio_path)[0]}.txt"
        with open(srt_path, "w", encoding="utf-8") as srt_file:
            with open(txt_path, "w", encoding="utf-8") as txt_file:
                for i, segment in enumerate(segments, start=1):
                    start = self.format_timestamp(segment.start)
                    end = self.format_timestamp(segment.end)
                    text = segment.text.strip()
                    print(f"{i}\n{start} --> {end}\n{text}\n", file=srt_file, flush=True)
                    print(f"{text}", file=txt_file, flush=True)

        self.to_screen(f"[{get_current_time()}] Transcription saved to {srt_path}")

        info["transcription"] = srt_path
        return [], info


# Add the post-processor to yt-dlp
def add_transcriber(ydl):
    ydl.add_post_processor(TranscriberPP())
