import json
import streamlit.components.v1 as components
import dotenv
dotenv.load_dotenv()
from langchain.chains.llm import LLMChain
from langchain.chat_models import ChatOpenAI
import streamlit as st
from youtube_search import YoutubeSearch
import yaml
import langchain
from langchain.cache import SQLiteCache
langchain.llm_cache = SQLiteCache(database_path=".langchain_cache.db")
import prompts
import default_submit
import numpy as np
import asyncio

def setup_player(playlist):
    components.html("""<div id="player"></div>
<script>
    var tag = document.createElement('script');
    tag.src = "https://www.youtube.com/iframe_api";
    var firstScriptTag = document.getElementsByTagName('script')[0];
    firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);
    var player;
    var playlist = PLAYLIST;
    var previousIndex = 0;
    function onYouTubeIframeAPIReady() {
        new YT.Player('player', {
            width: "100%",
            playlist: playlist,
            playerVars: {
            'playsinline': 1
            },
            events: {
                'onReady': onPlayerReady,
            }
        });
    }
    function onPlayerReady(event) {
        event.target.loadPlaylist(playlist)
        event.target.setLoop(true);
    }
</script>"""
        .replace("PLAYLIST", json.dumps(playlist)),
        height=360,
    )

@st.cache_data(show_spinner=False, hash_funcs={})
def search_youtube(item):
    search_results_ = []
    while len(search_results_) == 0:
        try:
            search_results_ = YoutubeSearch(item, max_results=5).to_dict()
        except Exception as e:
            print(e)
    search_results = ""
    i = 0
    for result in search_results_:
        search_results += f"Index {i}. {result['title']} METADATA: <duration: {result['duration']}, channel: {result['channel']}, views: {result['views'] }, publish_time: {result['publish_time']}>\n"
        i += 1
    index_yml = LLMChain(llm=ChatOpenAI(temperature=0, model="gpt-3.5-turbo", cache=True), prompt=prompts.extract_index).run({
        "search_results": search_results,
        "search_request": item,
    })
    index = yaml.load(index_yml, Loader=yaml.FullLoader)['index']
    print(f"""
    search_results: {search_results}
    search_request: {item}
    reasoning: {index_yml}
    """)

    try:
        id = search_results_[int(index)]['id']
    except:
        print(f"ERROR: {index} is not a valid index")
        id = search_results_[0]['id']
    return id
def show_playlist(playlist):
    st.markdown("### Playlist")
    playlist_formatted = []
    for item in playlist:
        if "\t" in item:
            item = item.replace("\t", " - ")
        item_formatted = f"{item}"
        playlist_formatted.append(item_formatted)
    
    st.code("\n".join(playlist_formatted), language="text")

async def submit(text_input, ids, min, status, progress):
    updated_items = []
    while len(updated_items) < min:
        result = LLMChain(llm=ChatOpenAI(temperature=1, model="gpt-3.5-turbo", cache=True), prompt=prompts.generate_playlist).run({
            "user_request": text_input,
            "min": min,
            "current_list": updated_items,
        })

        current_items = yaml.load(result, Loader=yaml.FullLoader)
        updated_items = updated_items + current_items
        if len(updated_items) > min:
            updated_items = updated_items[:min]
        np.random.shuffle(updated_items)

    st.session_state.current_playlist = updated_items
    show_playlist(st.session_state.current_playlist)
    status.update(label="Searching YouTube...", expanded=True)

    for item in updated_items:
        result = search_youtube(item)
        progress_value = (len(ids) + 1) / len(updated_items)
        item_text = item.replace("\t", " - ")
        progress.progress(progress_value, text=f"{len(ids) + 1} / {min}: {item_text}")
        ids.append(result)

    status.update(label="Complete!", state="complete", expanded=False)
    return ids

def main():
    st.title("BeatStream", anchor="title")
    st.markdown("""
    Created by Richard McSorley 
    [Email](mailto:rich@mcsorley.co)

    AI powered music playlist generator.
    """)
    
    example = st.button("Example")
    with st.form(key='playlist_form'):
        if "text_input_value" not in st.session_state:
            st.session_state.text_input_value = ""
        if "slider_value" not in st.session_state:
            st.session_state.slider_value = 5
        if "current_playlist" not in st.session_state:
            st.session_state.current_playlist = []
        if example:
            st.session_state.slider_value = 5
            st.session_state.text_input_value = default_submit.text_input
        
        text_input = st.text_area(
            "Your request",
            value=st.session_state.text_input_value,
            height=250,
            placeholder="Type your request here... \n\n'I want to listen to something that makes me feel happy, upbeat, and energetic.'",
        )
        ids = []
        min = st.slider("How many songs", min_value=2, max_value=50, value=st.session_state.slider_value, step=1)
        submitted = st.form_submit_button('Submit', type="primary")
        st.session_state.text_input_value = text_input
        st.session_state.slider_value = min
        if submitted or example:
            if len(text_input) > 0:   
                with st.status("Generating...", expanded=True) as status:
                    progress = st.progress(0, text=f"{len(ids)} / {min}")
                    asyncio.run(submit(text_input, ids, min, status, progress))
                if len(ids) > 0:
                    setup_player(ids)
                    st.markdown(f"""Not working? [Listen on Youtube Instead](https://www.youtube.com/watch_videos?video_ids={','.join(ids)})""")
                show_playlist(st.session_state.current_playlist)
            else:
                st.error("You must enter a request.")

if __name__ == "__main__":
    st.set_page_config({
        "page_title": "BeatStream",
        "page_icon": "🎵",
        "layout": "centered",
        "initial_sidebar_state": "auto",
    })
    main()
