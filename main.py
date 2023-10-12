import json
import streamlit.components.v1 as components
import dotenv
dotenv.load_dotenv()
from langchain import PromptTemplate
from langchain.chains.llm import LLMChain
from langchain.chat_models import ChatOpenAI
import streamlit as st
from youtube_search import YoutubeSearch
import yaml
import signal

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
        signal.alarm(5)
        search_results_ = YoutubeSearch(item, max_results=10).to_dict()
        signal.alarm(0)
        search_results = ""
        i = 0
        for result in search_results_:
            search_results += f"{i}. {result['title']} - duration {result['duration']}, channel {result['channel']}, views {result['views'] }, publish_time: {result['publish_time']}, index {i} \n"
            i += 1
        signal.alarm(5)
        index = LLMChain(llm=ChatOpenAI(temperature=0, model="gpt-3.5-turbo"), prompt=PromptTemplate(template="""
# MISSION
You will extract the matching index from the list of songs results from a youtube search.

# INPUT
- A song title and artist name we are looking for.
- A list of search results with index numbers.

# OUTPUT
- an integer that matches the index of the song title and artist name.

# RULES
- Do not leave any comments in the output.
- Do not list anything other than the index that matches the song title and artist name.
- If you cannot find the song title and artist name in the list of search results, output -1.
- If you are not sure just output -1.
- Avoid live performances, remixes, and covers, but if there are no other options, it's ok to select one of them.

## Example Output:
5

SEARCH REQUEST: {search_request}
SEARCH RESULTS: {search_results}

output:""",
    input_variables = [
        "search_results",
        "search_request",
        ],
    )).run({
        "search_results": search_results,
        "search_request": item,
    })
        signal.alarm(0)
        id = search_results_[int(index)]['id']
        return id
    except Exception as e:
        print(e)
        return None
def submit(options, text_input, ids, items, min):
    with st.status("Generating...", expanded=True) as status:
        result = LLMChain(llm=ChatOpenAI(temperature=1, model="gpt-3.5-turbo"), prompt=PromptTemplate(template="""
# MISSION
You are a expert music playlist generator. You craft the perfect playlists given a user's request.

# INPUT
- User has a freeform input, they may provide only a song name, an artist name, a genre, or any type of request such as "I want to listen to something that makes me feel happy" (optional field).
- User may also provide a list of genres they want to listen to (optional field).

# OUTPUT
- YAML format. The output will be a list of songs with their artist name.
- {min} songs, no more no less.

# RULES
- You can only output in YAML format. The output will be a list of songs with their artist name.
- Do not leave any comments in the output.
- Do not wite anything other than the list of songs with their artist name.
- Song name and artist name must be separated by a tab character.
- You must strip any unsafe unicode characters from the song name and artist name so it can be read by a yaml parser.

## Example Output:
- "I'm a slave 4 u\tBritney Spears"
- "Toxic\tBritney Spears"
- "Oops!... I Did It Again\tBritney Spears"

USER'S REQUEST: {user_request}
SELECTED GENRES (Optional): {genres}

output:""",
input_variables = ["user_request", "genres", "min"],
)).run({
            "user_request": text_input + " " + " ,".join(options),
            "genres": options,
            "min": min,
            })
        status.update(label="Searching YouTube...", state="running", expanded=True)
        items  = yaml.load(result, Loader=yaml.FullLoader)
        progess = st.progress(0, text="Searching Youtube...")
        ids = []
        d_i = 0
        for item in items:
            item_str = yaml.dump(item).replace("\\t", " - ").replace("\"", "")
            progess.progress((d_i + 1) / len(items), text=f"{d_i + 1} / {len(items)} | {item_str}")
            result = search_youtube(item)
            if result is None:
                continue
            d_i += 1
            ids.append(result)
        
    if len(items) == 0:
        st.write("No results found.")
    else:
        status.update(label="Complete!", state="complete", expanded=False)
    setup_player(ids)
    st.markdown(f"""[Listen on Youtube](https://www.youtube.com/watch_videos?video_ids={','.join(ids)})""")

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
        [
            'Pop',
            'Rock',
            'Rap',
            'Hip Hop',
            'R&B',
            'Country',
            'Jazz',
            'Classical',
            'Metal',
            'Electronic',
            'Funk',
            'Soul',
            'Disco',
            'Techno',
            'Dance',
            'KPop',
            'JPop',
            'Gaming',
            'Chill',
            'Chilstep',
            'LoFi',
            'Vaporwave',
            'Synthwave',
            'Retro',
            '80s',
            '90s',
            '00s',
            '10s',
            '20s',
        ],
        )
        min = st.slider("How many songs", min_value=2, max_value=50, value=5, step=1)
        submitted = st.form_submit_button('Submit', type="primary")
        if submitted:
            if len(options) > 0 or len(text_input) > 0:   
                submit(options, text_input, ids, items, min)
            else:
                st.write("You did not enter anything, so we'll generate some songs you can code to.")
                submit([], """I like this playlist of songs for programming:
The Chainsmokers - Don't Let Me Down (Illenium Remix)
L'indécis - Cloud Steps [Plethoria Album]
Raven & Kreyn - So Happy [NCS Official Video]
The Knocks - Brazilian Soul (feat. Sofi Tukker)
[Electro] - Fractal - Atrium [Monstercat Release]
Pixel Terror - Dilemma (feat. DYSON) [Monstercat Release]
Gammer & Darren Styles - DYSYLM [Monstercat Lyric Video]
Julian Calor - Arp of Astronomical Wisdom [Monstercat Release]
Feed Me - New Shoes [Monstercat Release]
Caspro - The Approach
MMV - You know what I'm like  (ﾉ*ФωФ)ﾉ
Infected Mushroom - Head of NASA [Monstercat LP Release]
Steam Phunk - Easy | Diversity Release
Winnetka Bowling League - Kombucha (BRKLYN REMIX)
UPSAHL - People I Don't Like
Slice N Dice - Let's Go (Original Mix) [ FREE DOWNLOAD]
Creaky Jackals - High Tide (feat. WILD) (Nurko Remix)
Create a new list that are related that I can add to it.""", ids, items, min)

if __name__ == "__main__":
    main()
