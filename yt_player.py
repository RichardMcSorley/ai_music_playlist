import streamlit.elements.media as media
from streamlit.proto.Video_pb2 import Video as VideoProto
import streamlit as st

def marshall_video(
    coordinates: str,
    proto,
    data,
    mimetype: str = "video/mp4",
    start_time: int = 0,
) -> None:
    youtube_url = data
    proto.url = youtube_url
    proto.type = VideoProto.Type.YOUTUBE_IFRAME


media.marshall_video = marshall_video

def yt_player(auto_play="1"):
    st.session_state['url'] = ''
    def render_video(playlist):
        first_video = None
        remaining_videos = None
        if len(playlist) == 0:
            return
        if len(playlist) == 1:
            first_video = playlist[0]
        else:
            first_video = playlist[0]
            remaining_videos = playlist[1:]
        if remaining_videos is None:
            st.session_state["url"] = f"https://www.youtube.com/embed/{first_video}?autoplay={auto_play}&loop=1"
        else:
            playlist_str = ",".join([first_video] + remaining_videos)
            st.session_state["url"] = f"https://www.youtube.com/embed/{first_video}?playlist={playlist_str}&autoplay={auto_play}&loop=1"
        st.video(st.session_state["url"])
        
    return render_video