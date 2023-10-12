from langchain.prompts import PromptTemplate
extract_index = PromptTemplate(template="""
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
    input_variables=["search_request", "search_results"],
)

generate_playlist = PromptTemplate(template="""
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
ALREADY_GENERATED_PLAYLIST: {current_list}

output:""",
    input_variables = ["user_request", "genres", "min", "current_list"],
)