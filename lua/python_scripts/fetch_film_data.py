'''
Fetch data from the tmdb3 database for a specified film or list of films

@author Garret Wilson
'''


import os
import sys
import subprocess
import requests
import json
import io
import tkinter as tk

from dotenv import load_dotenv
from tkinter import ttk, font
from typing import Any, TextIO
from requests import Response
from types import FrameType
from json import JSONDecodeError

load_dotenv()


LOG_FILE_NAME: str = "logs_python_script.txt"
LOG_FILE: TextIO = io.StringIO()        # temp place holder for easing type safety
LOG_CODES = {
    "error" : -1,
    "cancelled" : -2,
    "no_result" : -3
}
LOG_DELIM = f"\n\n {"=" * 125}\n"

URLS:dict[str, str] = {
    # expects title string
    "film_search" : "https://api.themoviedb.org/3/search/movie",

    # expects film id
    "film_details" : "https://api.themoviedb.org/3/movie/{}",
    "film_credits" : "https://api.themoviedb.org/3/movie/{}/credits",
    "film_videos" : "https://api.themoviedb.org/3/movie/{}/videos"
}

HEADERS: dict[str, str] = {
    "accept": "application/json",
    "Authorization": f"Bearer {os.getenv('API_READ_ACCESS_TOKEN')}"
}


def no_films_found_message(root: tk.Tk, spreadsheet_title: str):
    '''Spawns a window that informs the user no films with spreadsheet_title title
    was found in TMDb

    :param spreadsheet_title: title grabbed from sc-im spreadsheet
    '''
    # log first
    LOG_FILE.write("\n-- NO SEARCH RESULTS\n")
    LOG_FILE.write(f"--     Spreadsheet title: {spreadsheet_title}\n")
    LOG_FILE.write(LOG_DELIM)
    LOG_FILE.close()

    # spawn window
    popup: tk.Toplevel = tk.Toplevel(root)
    popup.title("Alert")
    popup.attributes(topmost=True)   # bring to front

    # top container in root for horizontal content (icon + message)
    content_frame_padding_x: int = 20
    content_frame_padding_y: int = 30
    content_frame = ttk.Frame(popup)
    content_frame.pack(padx=content_frame_padding_x, pady=content_frame_padding_y)

    # add a frame widget in content frame and put icon in it
    icon_frame: ttk.Frame = ttk.Frame(content_frame)
    icon_frame.pack(side="left")
    icon_text: str = "🛑"
    icon_font = font.Font(size=36)
    ttk.Label(icon_frame, text=icon_text, font=icon_font).grid(row=0, column=0, sticky="w")

    # add a frame widget to content frame put message in it
    message_frame: ttk.Frame = ttk.Frame(content_frame)
    message_frame.pack(side="left")
    message_text: str = "No films with this title were found in TMDb\n"
    message_font: font.Font = font.Font(family="Arial", size=12)
    title_text: str = spreadsheet_title
    title_font: font.Font = font.Font(family="Arial", size=14, weight="bold")
    title_text_size: int = title_font.measure(title_text)
    message_padding_x: int = 20
    ttk.Label(message_frame, text=message_text, font=message_font).grid(row=0, column=1, sticky="w", padx=message_padding_x)
    ttk.Label(message_frame, text=title_text, font=title_font).grid(row=1, column=1, sticky="w", padx=message_padding_x)

    # add a frame widget to root to put button in
    button_frame: ttk.Frame = ttk.Frame(popup, padding=10)
    button_frame.pack(fill="x")
    ttk.Button(button_frame, text="OK", command=popup.destroy).pack(expand=True, anchor="e", padx=10)

    # set size of window dynamically with respect to title width if its large
    default_width: int = 450
    defualt_height: int = 175
    if title_text_size + content_frame_padding_x * 2 + message_padding_x * 2 > default_width:
        root_padding = icon_font.measure("🛑") + (message_padding_x * 2) + (content_frame_padding_x * 2)
        popup.geometry(f"{title_text_size + root_padding}x{defualt_height}")
        popup.minsize(title_text_size+root_padding, defualt_height)
        popup.maxsize(title_text_size+root_padding, defualt_height)
    else:
        popup.geometry(f"{default_width}x{defualt_height}")
        popup.minsize(default_width, defualt_height)
        popup.maxsize(default_width, defualt_height)

    popup.wait_window()

    print(LOG_CODES["no_result"], end="")
    sys.exit(0)


def ask_film_choice(root: tk.Tk, opts: list[str], spreadsheet_title: str) -> int:
    '''Spawns an input window that list the film options a user can choose between

    :param opts: List of movie titles and release date
    :return: Index (by 1) of movie chosen by user
    '''
    # spawn window
    popup: tk.Toplevel = tk.Toplevel(root)
    popup.title("Choose Film")
    popup.attributes(topmost=True)

    # add a messaage frame inside root window
    message_frame: ttk.Frame = ttk.Frame(popup)
    message_frame.pack(fill="x", expand=True, padx=20, pady=10)
    icon_text: str = "⚠️"
    icon_font: font.Font = font.Font(size=24)
    message_text: str = "Multiple films found. Please choose one from below"
    message_font: font.Font = font.Font(family="Arial", size=12)
    ttk.Label(message_frame, text=icon_text, font=icon_font).pack(side="left")
    ttk.Label(message_frame, text=message_text, font=message_font).pack(side="left", padx=20)

    # add a litbox frame inside root window
    listbox_frame: ttk.Frame = ttk.Frame(popup)
    listbox_frame.pack(fill="both", expand=True)
    list_element_font: font.Font = font.Font(family="Arial", size=12)
    listbox: tk.Listbox = tk.Listbox(popup, selectmode=tk.SINGLE, height=10, font=list_element_font, activestyle="none", relief="raised", borderwidth=5)
    listbox.pack(fill="both", expand=True, padx=20)
    max_element_width: int = 0
    for film in opts:
        list_element_width = list_element_font.measure(film)
        if list_element_width > max_element_width:
            max_element_width = list_element_width
        listbox.insert(tk.END, film)

    # add a button frame inside root window
    button_frame: ttk.Frame = ttk.Frame(popup, padding=10)
    button_frame.pack(fill="x")

    # function for cancel button to use
    def cancel_selecction():
        nonlocal index
        LOG_FILE.write("\n-- CANCELLED\n")
        LOG_FILE.write("--      Popup: choose film\n")
        LOG_FILE.write(f"--      Spreadsheet title: {spreadsheet_title}\n")
        LOG_FILE.write(LOG_DELIM)
        print(LOG_CODES["cancelled"], end="")
        index = -1
        popup.destroy()

    # function for select button to use
    index: int = 0
    def get_selected_index():
        nonlocal index
        if listbox.curselection():
            index = listbox.curselection()[0]
        popup.destroy()

    ttk.Button(button_frame, text="Cancel", command=cancel_selecction).pack(side="right", padx=10)
    ttk.Button(button_frame, text="Select film", command=get_selected_index).pack(side="right")

    # dynamically adjust window width for longest title
    popup.geometry(f"{max_element_width + 75}x350")

    popup.wait_window()

    return index


# def ask_title_change(root: tk.Tk, curr_title: str) -> str:
#     '''Spawns an input window that asks the user if they want to change the film title
#
#     :param curr_title: Title of movie user selected
#     :return: str of title chosen
#     '''
#     popup: tk.Toplevel = tk.Toplevel(root)
#     popup.title("Change film name?")
#     popup.attributes(topmost=True)
#
#     #
#     # SCRAPPED
#     #
#
#     return ""


def film_search(root: tk.Tk, spreadsheet_title: str) -> str | None:
    '''Fetch the results of searching tmdb for a film. Can contain multiple results

    :param search_title: Title from the sc-im spreasheet
    :return: tuple containing the chosen film title and that films id or None
    '''
    # config
    frame: FrameType = sys._getframe()

    # make request to search for film and log it
    query_data: dict[str, str] = {"query" : spreadsheet_title, "include_adult" : "false", "language" : "en-US", "page" : "1"}
    request_line: int = frame.f_lineno + 1
    response: Response = requests.get(URLS["film_search"], params=query_data, headers=HEADERS)
    LOG_FILE.write("\n-- REQUEST\n")
    LOG_FILE.write(f"--     URL: {response.url}\n")
    LOG_FILE.write(f"--     Response code: {response.status_code}\n")
    LOG_FILE.flush()
    if 300 <= response.status_code < 200:
        LOG_FILE.write("-- [ERROR] BAD RESPONSE\n")
        LOG_FILE.write(f"--     Function: {frame.f_code.co_name}\n")
        LOG_FILE.write(f"--     Line: {request_line}\n")
        LOG_FILE.write(f"--     Reponse text: {response.text}\n")
        LOG_FILE.write(LOG_DELIM)
        LOG_FILE.close()
        print(LOG_CODES["error"], end="")
        sys.exit(1)

    # try to create python object from JSON
    json_decode_line: int = frame.f_lineno + 2
    try:
        json_data: dict[str, Any] = json.loads(response.text)
    except JSONDecodeError:
        LOG_FILE.write("\n-- [ERROR] JSON DECODE\n")
        LOG_FILE.write(f"--     Function: {frame.f_code.co_name}\n")
        LOG_FILE.write(f"--     Line: {json_decode_line}\n")
        LOG_FILE.write(f"--     Response text:\n{response.text}\n")
        LOG_FILE.write(LOG_DELIM)
        LOG_FILE.close()
        print(LOG_CODES["error"], end="")
        sys.exit(1)

    # no search results for the spreadsheet title grabbed
    if len(json_data["results"]) == 0:
        no_films_found_message(root, spreadsheet_title)

    # if more than one result, allow user to choose film
    index: int = 0
    if len(json_data["results"]) > 1:
        film_list: list[dict[str, Any]] = json_data["results"]

        # build AppleScript list
        opts: list[str] = []
        for f in film_list:
            cleaned_title = f["title"].replace('"', '\\"')
            opts.append(f"{cleaned_title} ({f['release_date']})")

        index = ask_film_choice(root, opts, spreadsheet_title)
        if index == -1:
            return None

    film_id: str = json_data["results"][index]["id"]

    return film_id


def parse_film_title(res_dict: dict[str, Any], key: str, details_json_data: dict[str, Any]):
    '''Parses the films title from the details data and assigns them to respective
    key in the result dictionary

    :param res_dict: Result dictionary where data is stored
    :param key: Dictionary key to write to
    :param details_json_data: json formatted details data
    '''
    res_dict[key] = details_json_data["original_title"]


def parse_film_genres(res_dict: dict[str, Any], key: str, details_json_data: dict[str, Any]) -> None:
    '''Parses the films genre(s) from the details data and assigns them to respective
    key in the result dictionary

    :param res_dict: Result dictionary where data is stored
    :param key: Dictionary key to write to
    :param details_json_data: json formatted details data
    '''
    # genre element is an array of objects
    genre_list = []
    genres: list[dict[str, Any]] = details_json_data["genres"]
    for genre in genres:
        if genre["name"]:
            genre_list.append(genre["name"])

    res_dict[key]= genre_list


def parse_film_release_date(res_dict: dict[str, Any], key: str, details_json_data: dict[str, Any]) -> None:
    '''Parse the films release date and assign it to respective key in
    result dictionary

    :param res_dict: Result dictionary where data is written
    :param key: Dictionary key to write to
    :param details_json_data: json formatted details data
    '''
    # release date is a single str
    res_dict[key]= details_json_data["release_date"] if details_json_data["release_date"] else None


def parse_film_runtime(res_dict: dict[str, Any], key:str, details_json_data: dict[str, Any]) -> None:
    '''Parse the films runtime and assign it to respective key in result 
    dictionary

    :param res_dict: Result dictionary where data is written
    :param key: Dictionary key to write to
    :param details_json_data: json formatted details data
    '''
    # runtime is a single int in minutes
    res_dict[key] = details_json_data["runtime"] if details_json_data["runtime"] else None


def parse_film_studios(res_dict: dict[str, Any], key: str, details_json_data: dict[str, Any]) -> None:
    '''Parses the films studios(s) from the details data and assigns them to respective
    key in the result dictionary

    :param res_dict: Result dictionary where data is stored
    :param key: Dictionary key to write to
    :param details_json_data: json formatted details data
    '''
    # studios is a array of objects
    studio_list = []
    studios: list[dict[str, Any]] = details_json_data["production_companies"]
    for studio in studios:
        if studio["name"]:
            studio_list.append(studio["name"])

    res_dict[key] = studio_list


def parse_film_directors(res_dict, key, credits_json_data) -> None:
    '''Parses the films directors(s) from the credits data and assigns them to respective
    key in the result dictionary

    :param res_dict: Result dictionary where data is stored
    :param key: Dictionary key to write to
    :param details_json_data: json formatted credits data
    '''
    # crew is an array of objects
    crew: list[dict[str, Any]] = credits_json_data["crew"]

    # director(s), writer(s), and composer(s) are apart of the crew
    director_list = []
    for crew_member in crew:
        job: str = crew_member["job"]
        if job and job == "Director":
            director_list.append(crew_member["name"])

    res_dict[key] = director_list


def parse_film_writers(res_dict, key, credits_json_data) -> None:
    '''Parses the films writers(s) from the credits data and assigns them to respective
    key in the result dictionary

    :param res_dict: Result dictionary where data is stored
    :param key: Dictionary key to write to
    :param details_json_data: json formatted credits data
    '''
    # crew is an array of objects
    crew: list[dict[str, Any]] = credits_json_data["crew"]

    # director(s), writer(s), and composer(s) are apart of the crew
    writer_list = []
    for crew_member in crew:
        job: str = crew_member["job"]
        if job and (job == "Writer" or job == "Story"):
            writer_list.append(crew_member["name"])

    res_dict[key] = writer_list


def parse_film_cast(res_dict, key, credits_json_data) -> None:
    '''Parses the films cast from the credits data and assigns them to respective
    key in the result dictionary

    :param res_dict: Result dictionary where data is stored
    :param key: Dictionary key to write to
    :param details_json_data: json formatted credits data
    '''
    # cast is an array of objects
    cast: list[dict[str, Any]] = credits_json_data["cast"]

    # save 15 cast members or the length of cast
    limit: int = 15 if len(cast) > 15 else len(cast)
    cast_list = []
    for i in range(0, limit):
        if cast[i]["name"]:
            cast_list.append(cast[i]["name"])

    res_dict[key] = cast_list


def parse_film_composers(res_dict, key, credits_json_data) -> None:
    '''Parses the films composer(s) from the credits data and assigns them to respective
    key in the result dictionary

    :param res_dict: Result dictionary where data is stored
    :param key: Dictionary key to write to
    :param details_json_data: json formatted credits data
    '''
    # crew is an array of objects
    crew: list[dict[str, Any]] = credits_json_data["crew"]

    # director(s), writer(s), and composer(s) are apart of the crew
    composer_list = []
    for crew_member in crew:
        job: str = crew_member["job"]
        if job and job == "Original Music Composer":
            composer_list.append(crew_member["name"])

    res_dict[key] = composer_list


def ask_user_input(res_dict: dict[str, Any], peronal_keys: list[str]) -> None:
    '''Ask the user input via an AppleScript popup window. The user related features are:

        RATING, WATCHED (# times), LAST WATCHED, NOTES

    and assigns them to that key in the result dictionary

    :param res_dict: result dictionary where data is stored
    '''

    # TODO

    pass


def film_data_json(feat_names: list[str], film_id: str) -> str:
    '''Organizes film data fetched into a Python dict, encodes to a JSON object, and returns
    a string of the JSON object

    Details:    GENRE(S), RELEASE DATE, RUNTIME (M), STUDIO(S)

    Credits:    DIRECTOR(S), WRITER(S), CAST, COMPOSER(S)

    Video:      TODO

    Personal:   RATING, WATCHED (# times), LAST WATCHED, NOTES

    :param feat_names: Feature names currently in the sc-im spreadsheet
    :param film_id: Unique id for the film
    :param film_title: Updated title if user edited it or original title
    :return: str of JSON object
    '''
    # config
    frame: FrameType = sys._getframe()

    # create dict with feature names
    res_dict: dict[str, Any] = {}
    for name in feat_names:
        res_dict[name] = None

    # make the film details requets and store response
    details_json_data: dict[str, Any] = {}
    details_query_data: dict[str, str] = {"language" : "en_US"}
    details_request_line = frame.f_lineno + 1
    details_response: Response = requests.get(URLS["film_details"].format(film_id), params=details_query_data, headers=HEADERS)
    LOG_FILE.write("\n-- REQUEST\n")
    LOG_FILE.write(f"--     URL: {details_response.url}\n")
    LOG_FILE.write(f"--     Response code: {details_response.status_code}\n")
    LOG_FILE.flush()
    if 300 <= details_response.status_code < 200:
        LOG_FILE.write("-- [ERROR] BAD RESPONSE\n")
        LOG_FILE.write(f"--     Function: {frame.f_code.co_name}\n")
        LOG_FILE.write(f"--     Line: {details_request_line}\n")
        LOG_FILE.write(f"--     Response text: {details_response.text}\n")
    else:
        details_json_decode_line = frame.f_lineno + 2
        try:
            details_json_data: dict[str, Any] = json.loads(details_response.text)
        except JSONDecodeError:
            details_json_data = {}
            LOG_FILE.write("\n-- [ERROR] JSON DECODE\n")
            LOG_FILE.write(f"--     Function: {frame.f_code.co_name}\n")
            LOG_FILE.write(f"--     Line: {details_json_decode_line}\n")
            LOG_FILE.write(f"--     Response text:\n{details_response.text}\n")
            LOG_FILE.close()

    # make the film credits request and store response
    credits_json_data: dict[str, Any] = {}
    credits_query_data: dict[str, str] = {"language" : "en-US"}
    credits_request_line = frame.f_lineno + 1
    credits_response: Response = requests.get(URLS["film_credits"].format(film_id), params=credits_query_data, headers=HEADERS)
    LOG_FILE.write("\n-- REQUEST\n")
    LOG_FILE.write(f"--     URL: {credits_response.url}\n")
    LOG_FILE.write(f"--     Response code: {credits_response.status_code}\n")
    LOG_FILE.flush()
    if 300 <= details_response.status_code < 200:
        LOG_FILE.write("-- [ERROR] BAD RESPONSE\n")
        LOG_FILE.write(f"--     Function: {frame.f_code.co_name}\n")
        LOG_FILE.write(f"--     Line: {credits_request_line}\n")
        LOG_FILE.write(f"--     Response text: {credits_response.text}\n")
        LOG_FILE.close()
    else:
        credits_json_decode_line = frame.f_lineno + 2
        try:
            credits_json_data: dict[str, Any] = json.loads(credits_response.text)
        except JSONDecodeError:
            credits_json_data = {}
            LOG_FILE.write("\n-- [ERROR] JSON DECODE\n")
            LOG_FILE.write(f"--     Function: {frame.f_code.co_name}\n")
            LOG_FILE.write(f"--     Line: {credits_json_decode_line}\n")
            LOG_FILE.write(f"--     Response text:\n{credits_response.text}\n")
            LOG_FILE.close()

    videos_query_data: dict[str, str] = {"language" : "en-US"}
    videos_response = ""
    videos_json_data = ""

    # call functions that will fill their respective keys with values
    peronal_keys = ["RATING", "WATCHED (# times)", "LAST WATCHED", "NOTES"]
    for key,value in res_dict.items():

        # details
        if key == "FILM":
            parse_film_title(res_dict, key, details_json_data)
        elif key == "GENRE(S)":
            parse_film_genres(res_dict, key, details_json_data)
        elif key == "RELEASE DATE":
            parse_film_release_date(res_dict, key, details_json_data)
        elif key == "RUNTIME (M)":
            parse_film_runtime(res_dict, key, details_json_data)
        elif key == "STUDIO(S)":
            parse_film_studios(res_dict, key, details_json_data)

        # credits
        elif key == "DIRECTOR(S)":
            parse_film_directors(res_dict, key, credits_json_data)
        elif key == "WRITER(S)":
            parse_film_writers(res_dict, key, credits_json_data)
        elif key == "CAST":
            parse_film_cast(res_dict, key, credits_json_data)
        elif key == "COMPOSER(S)":
            parse_film_composers(res_dict, key, credits_json_data)

        # video
        elif key == "LINK":
            pass

        # personal
        elif key in peronal_keys:
            ask_user_input(res_dict, peronal_keys)

    LOG_FILE.write("\n-- RESULT\n")
    LOG_FILE.write(f"--     Python dictionary: {str(res_dict)}\n")

    return json.dumps(res_dict)


def main():
    # setup
    global LOG_FILE
    root: tk.Tk = tk.Tk()
    root.withdraw()

    # check has feature names, title args, and log mode
    if len(sys.argv) != 4:
        LOG_FILE = open(LOG_FILE_NAME, "w")
        LOG_FILE.write("\n-- [ERROR] INVOCATION\n")
        LOG_FILE.write("--      Usage: python3 fetch_film_data.py [feat_names] [search_title] [log_file_mode]\n")
        LOG_FILE.write(f"--      Invocation: python3 fetch_film_data.py {' '.join([arg for arg in sys.argv])}")
        LOG_FILE.close()
        sys.exit(1)

    # make a list of feature names
    feat_names: list[str] = sys.argv[1].split(",")

    # get spreadsheet title
    spreadsheet_title: str = sys.argv[2].strip()

    # open log file depending on mode arg
    if sys.argv[3] == "a":
        LOG_FILE = open(LOG_FILE_NAME, "a")
    elif sys.argv[3] == "w":
        LOG_FILE = open(LOG_FILE_NAME, "w")
    else:
        sys.exit(1)

    LOG_FILE.write("\n-- SPREADSHEET TITLE\n")
    LOG_FILE.write(f"--      title: {spreadsheet_title}\n")

    film_id = film_search(root, spreadsheet_title)
    if film_id is None:
        LOG_FILE.write(LOG_DELIM)
    else:
        # printing sends data to Lua script
        print(film_data_json(feat_names, film_id))
        LOG_FILE.write(LOG_DELIM)

    root.destroy()


if __name__ == "__main__":
    main()

