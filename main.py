import dotenv
dotenv.load_dotenv()
from langchain.chains.llm import LLMChain
from langchain.chat_models import ChatOpenAI
import streamlit as st
from youtube_search import YoutubeSearch
import yaml
import langchain
from langchain.cache import SQLiteCache
langchain.llm_cache = SQLiteCache(database_path=".cache_storage/langchain_cache.db")
import prompts
import examples
import numpy as np
from yt_player import yt_player

@st.cache_data(show_spinner=False, ttl=60*60*24*7)
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
    index = None
    try:
        index_yml = LLMChain(llm=ChatOpenAI(temperature=0, model="gpt-3.5-turbo", cache=True), prompt=prompts.extract_index).run({
            "search_results": search_results,
            "search_request": item,
        })
        index = yaml.load(index_yml, Loader=yaml.FullLoader)['index']
        print(f"""
        search_results: {search_results}
        search_request: {item}
        {index_yml}
        """)
    except Exception as e:
        print(e)
        index = 0
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

def submit(ids, status, progress):
    st.session_state.complete_search = False
    st.session_state.first_video_play = False
    updated_items = []
    while len(updated_items) < st.session_state.slider_value:
        result = LLMChain(llm=ChatOpenAI(temperature=1, model="gpt-3.5-turbo", cache=True), prompt=prompts.generate_playlist).run({
            "user_request": st.session_state.text_input_value,
            "min": st.session_state.slider_value,
            "current_list": updated_items,
        })
        current_items = yaml.load(result, Loader=yaml.FullLoader)
        updated_items = updated_items + current_items
        # remove duplicates
        updated_items = list(set(updated_items))

        if len(updated_items) > st.session_state.slider_value:
            updated_items = updated_items[:st.session_state.slider_value]
        np.random.shuffle(updated_items)

    st.session_state.current_playlist = updated_items
    show_playlist(st.session_state.current_playlist)
    status.update(label="Searching YouTube...", expanded=True)

    for item in updated_items:
        result = search_youtube(item)
        progress_value = (len(ids) + 1) / len(updated_items)
        item_text = item.replace("\t", " - ")
        progress.progress(progress_value, text=f"{len(ids) + 1} / {st.session_state.slider_value}: {item_text}")
        ids.append(result)
        if len(ids) >= 1 and st.session_state.first_video_play == False:
            st.session_state.first_video_play = True
            player = yt_player(auto_play="0")
            st.write("Playing first song, while we wait...")
            player([ids[0]])

    status.update(label="Complete!", state="complete", expanded=False)
    st.session_state.complete_search = True
    return ids
def show_example(example):
    # st.session_state["example_" + str(num)] = False
    button = None
    with example["col"]:
        button = st.button(example["title"])
    if button:
        st.session_state.text_input_value = example["prompt"]
        st.session_state.slider_value = 5

def main():
    st.markdown("""
    # :musical_note: BeatStream :musical_note:
    
    Created by Richard McSorley 
    [Email](mailto:rich@mcsorley.co)
    & -Corruption [Discord](https://discord.com/users/740502046578311170)

    AI powered music playlist generator.
    See an example by clicking one of the buttons below.

    Feel free to adjust the request and number of songs.
    """)
    
    if "text_input_value" not in st.session_state:
        st.session_state.text_input_value = ""
    if "slider_value" not in st.session_state:
        st.session_state.slider_value = 5
    if "current_playlist" not in st.session_state:
        st.session_state.current_playlist = []
    for example in examples.get_examples():
        show_example(example)
    with st.form(key='playlist_form'):
        new_text_input_value = st.text_area(
            "Your request",
            value=st.session_state.text_input_value,
            height=250,
            placeholder="Type your request here... \n\n'I want to listen to something that makes me feel happy, upbeat, and energetic.'",
        )
        st.session_state.text_input_value = new_text_input_value
        ids = []
        new_slider_value = st.slider("How many songs", min_value=5, max_value=50, value=st.session_state.slider_value, step=5)
        st.session_state.slider_value = new_slider_value
        submitted = st.form_submit_button('Submit', type="primary")
        if submitted:
            if len(st.session_state.text_input_value) > 0:   
                with st.status("Generating...", expanded=True) as status:
                    placeholder = st.empty()
                    progress = placeholder.progress(0, text=f"{len(ids)} / {st.session_state.slider_value}")
                    ids = submit(ids, status, progress)
                    placeholder.empty()
                if len(ids) > 0:
                    player = yt_player()
                    player(ids)
                    st.markdown(f"""Not working? [Listen on Youtube Instead](https://www.youtube.com/watch_videos?video_ids={','.join(ids)})""")
                show_playlist(st.session_state.current_playlist)
            else:
                st.error("You must enter a request.")

if __name__ == "__main__":
    st.set_page_config(
        page_title="BeatStream",
        page_icon="🎵",
        layout="centered",
        initial_sidebar_state="collapsed",
    )
    main()
