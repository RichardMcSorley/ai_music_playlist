from langchain.prompts import PromptTemplate
extract_index = PromptTemplate(template="""
# MISSION
You will extract the matching index from the list of songs results from a youtube search.

# INPUT
- A song title and artist name we are looking for.
- A list of search results with index numbers.

# OUTPUT
- an integer that matches the index of the song title and artist name.
- List of Reasonings for why this is the correct/incorect index
    Imagine three different experts are answering this question.
    All experts will write down 1 step of their thinking,
    then share it with the group.
    Then all experts will go on to the next step. Every index must be discussed by all experts.

# RULES
- Do not leave any comments in the output except for the reasoning list.
- Do not list anything other than the index that matches the song title and artist name.
- Avoid live performances, remixes, lyric videos, intramental, long videos, covers, karaoke, choreography, live streams, radio, 24/7, full albums.
- Official music videos are preferred.
- if some results match, make an educated guess on which one is the best match if possible, even if its one we should avoid.

## Example Output:
reasoning:
    # list of reasons why or why not each index is a good match or not
    - "Expert 1: index 0 we should avoid live performances"
    - "Expert 2: index 1 we should avoid long videos"
    - "Expert 3: index 2 is a good match because it is the official music video"
    - "Expert 1: index 3 is a good match because it is the radio edit of the song"
    - "Expert 2: index 4 we should avoid lyric videos"
    ...
index: 2

SEARCH REQUEST: {search_request}
SEARCH RESULTS: {search_results}

output:""".strip(),
    input_variables=["search_request", "search_results"],
)

generate_playlist = PromptTemplate(template="""
# MISSION
You are a expert music DJ. You craft the perfect playlists given a user's request.
You have worked in the industry for 10+ years crafting playlists for clubs and events.

# INPUT
- User has a freeform input, they may provide only a song name, an artist name, a genre, or any type of request such as "I want to listen to something that makes me feel happy" (optional field).
- User may also provide a list of genres they want to listen to (optional field).

# OUTPUT
- YAML format. The output will be a list of songs with their artist name.
- {min} songs, no more no less.

## Example Output:
- "I'm a slave 4 u\tBritney Spears"
- "Toxic\tBritney Spears"
- "Oops!... I Did It Again\tBritney Spears"

# RULES
- You can only output in YAML format. The output will be a list of songs with their artist name.
- Do not leave any comments in the output.
- Do not wite anything other than the list of songs with their artist name.
- Song name and artist name must be separated by a tab character.
- You must match the provided genre(s).
- Do not produce any duplicates.
- Avoid live performances, remixes, lyric videos, intramental, long videos, covers, karaoke, choreography, live streams, radio, 24/7, full albums.

USER REQUEST: {user_request}

ALREADY_GENERATED_PLAYLIST: {current_list}

output:""".strip(),
    input_variables = ["user_request", "min", "current_list"],
)