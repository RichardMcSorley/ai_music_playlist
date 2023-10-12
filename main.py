import json
import streamlit.components.v1 as components
import dotenv
dotenv.load_dotenv()
from langchain.chains.llm import LLMChain
from langchain.chat_models import ChatOpenAI
import streamlit as st
from youtube_search import YoutubeSearch
import yaml
import signal
import langchain
from langchain.cache import SQLiteCache
langchain.llm_cache = SQLiteCache(database_path=".langchain_cache.db")
import prompts
import genres
import default_submit
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError


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
        event.target.setShuffle(true);
        event.target.setLoop(true);
    }
</script>"""
        .replace("PLAYLIST", json.dumps(playlist)),
        height=360,
    )

def search_youtube(item):
    try:
        search_results_ = YoutubeSearch(item, max_results=10).to_dict()
        search_results = ""
        i = 0
        for result in search_results_:
            search_results += f"{i}. {result['title']} - duration {result['duration']}, channel {result['channel']}, views {result['views'] }, publish_time: {result['publish_time']}, index {i} \n"
            i += 1
        index = LLMChain(llm=ChatOpenAI(temperature=0, model="gpt-3.5-turbo", cache=True), prompt=prompts.extract_index).run({
            "search_results": search_results,
            "search_request": item,
        })
        id = search_results_[int(index)]['id']
        return id
    except Exception as e:
        print(e)
        return None

def submit(options, text_input, ids, items, min):
    with st.status("Generating...", expanded=True) as status:
        while len(items) < min:
            result = LLMChain(llm=ChatOpenAI(temperature=1, model="gpt-3.5-turbo", cache=True), prompt=prompts.generate_playlist).run({
                "user_request": text_input + " " + " ,".join(options),
                "genres": options,
                "min": min,
                "current_list": items,
            })
            current_items  = yaml.load(result, Loader=yaml.FullLoader)
            items = items + current_items
        if len(items) > min:
            items = items[:min]
        status.update(label="Searching YouTube...", expanded=True)

        progress = st.progress(0, text="Searching Youtube...")
        ids = []
        d_i = 0
        items_strs = []
        for item in items:
            item_str = yaml.dump(item).replace("\\t", " - ").replace("\"", "")
            items_strs.append(item_str)
        futures_to_item = {}
        with ThreadPoolExecutor() as executor:
            # Submit tasks and store future objects in a dictionary
            for item in items_strs:
                futures_to_item[executor.submit(search_youtube, item)] = item
                try:
                    # Process completed tasks, with a timeout of 5 seconds for each
                    for future in as_completed(futures_to_item, timeout=2):
                        item = futures_to_item[future]
                        result = future.result()
                        if result is None:
                            continue
                        progress.progress(len(ids) / (len(items) - 1), text=f"{len(ids) - 1} / {len(items)} | {item_str}")
                        d_i += 1
                        ids.append(result)
                except TimeoutError:
                    print("Some tasks took too long to complete.")

        
    if len(items) == 0:
        st.write("No results found.")
    else:
        status.update(label="Complete!", state="complete", expanded=False)
    setup_player(ids)
    st.markdown(f"""Not working? [Listen on Youtube Instead](https://www.youtube.com/watch_videos?video_ids={','.join(ids)})""")

def main():
    st.header("AI Music Playlist Generator")
    st.markdown("""
    Created by Richard McSorley 
    [Email](mailto:rich@mcsorley.co)

    Type any request. (e.g. 'I want to listen to something that makes me feel happy, upbeat, and energetic.')""")
    with st.form(key='playlist_form'):
        text_input = st.text_area(
            "Your request (Optional)",
        )
        ids = []
        items = []
        options = st.multiselect(
            'Select genre(s) (Optional)',
            genres.options
        )
        min = st.slider("How many songs", min_value=2, max_value=50, value=5, step=1)
        submitted = st.form_submit_button('Submit', type="primary")
        if submitted:
            if len(options) > 0 or len(text_input) > 0:   
                submit(options, text_input, ids, items, min)
            else:
                st.write("You did not enter anything, so we'll generate some songs you can code to.")
                submit([], default_submit.text_input, ids, items, min)

if __name__ == "__main__":
    main()
