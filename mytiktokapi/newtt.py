
class TikTokLoad():
    def get_video_by_url(self, video_url) -> bytes:
    """Downloads a TikTok video by a URL

    ##### Parameters
    * video_url: The TikTok url to download the video from
    """
    tiktok_schema = self.get_tiktok_by_url(video_url)
    download_url = tiktok_schema["itemInfo"]["itemStruct"]["video"]["downloadAddr"]

    return self.get_bytes(url=download_url)