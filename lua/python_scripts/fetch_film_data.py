'''
Fetch data from the tmdb3 database for a specified film or list of films

@author Garret Wilson
'''


import os
import sys
import subprocess
import requests
import json

from dotenv import load_dotenv
from colorama import init, Fore
from typing import Any

load_dotenv()

URLS:dict[str, str] = {
    "film_search" : "https://api.themoviedb.org/3/search/movie?query={}&include_adult=false&language=en-US&page=1",
    "film_details" : "https://api.themoviedb.org/3/movie/{}?language=en-US",
    "film_credits" : "https://api.themoviedb.org/3/movie/{}/credits?language=en-US",
    "film_videos" : "https://api.themoviedb.org/3/movie/{}/videos?language=en-US"
}

HEADERS: dict[str, str] = {
    "accept": "application/json",
    "Authorization": f"Bearer {os.getenv('API_READ_ACCESS_TOKEN')}"
}


def ask_film_index(opts: list[str]) -> int:
    '''Spawns an input window that list the film options a user can choose between

    :param opts: list of movie titles and release date
    :return: index (by 1) of movie chosen by user
    '''
    # format the options for the AppleScript
    applescript_list = "{" + ', '.join(opts) + "}"

    # osascript, AppleScript
    script = f'''
    tell application "System Events"
        activate
        set chosen to choose from list {applescript_list} with title "Movie Matcher" with prompt "Multiple movies found. Please choose:"
        if chosen is false then
            return "CANCELLED"
        else
            return item 1 of chosen
        end if
    end tell
    '''

    process = subprocess.Popen(['osascript', '-e', script], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    stdout, _ = process.communicate()

    # user pressedd cancel on pop up window
    if stdout.strip() == "CANCELLED":
        sys.exit(0)

    left_idx = stdout.find('[')
    right_idx = stdout.find(']')
    return int(stdout[left_idx + 1 : right_idx])


def ask_title_change(curr_title: str) -> str:
    '''Spawns an input window that asks the user if they want to change the film title

    :param search: tmdb object
    :param index: index of movie title chosen
    '''
    script = f'''
    tell application "System Events"
        activate
        display dialog "Do you want to change the name of \\"{curr_title}\\"?\\n\\nNew title:" with title "Rename Title" default answer "" buttons {{"Skip", "Confirm"}} default button "Confirm"
        if button returned of result is "Skip" then
            return "SKIPPED"
        else
            return text returned of result
        end if
    end tell
    '''

    process = subprocess.Popen(['osascript', '-e', script], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    stdout, _ = process.communicate()

    result = stdout.strip()
    if result == "SKIPPED" or result == "":
        return curr_title
    else:
        return result


def search_for_film(search_title: str) -> tuple[str, int]:
    # search for film
    response = requests.get(URLS["film_search"].format(search_title), headers=HEADERS)
    json_data: dict[str, Any] = json.loads(response.text)

    # if more than one result, allow user to choose film
    index: int = 0
    if len(json_data["results"]) > 1:
        film_list: list[dict[str, Any]] = json_data["results"]
        count: int = 0

        # build AppleScript list
        opts: list[str] = []
        for f in film_list:
            opts.append(f'"[{count+1}] {f['title']} ({f['release_date']})"')
            count += 1

        # index in pop up window is by 1, so need to 0 index
        index = ask_film_index(opts) - 1

    # grab film title (or new one given by user) and its id
    film_title: str = ask_title_change(json_data["results"][index]["title"])
    film_id: int = json_data["results"][index]["id"]

    return (film_title, film_id)


def get_film_details(res_dict: dict[str, Any]) -> None:
    '''Fetches the films details the spreadsheet tracks:

        GENRE(S), RELEASE DATE, RUNTIME, STUDIO(S)

    and assignss them to that key in the result dictionary

    :param res_dict: result dictionary where data is stored
    '''
    pass


def get_film_credits(res_dict: dict[str, Any]) -> None:
    '''Fetches the fillms credits the spreadsheet tracks:

        DIRECTOR(S), WRITER(S), CAST, COMPOSER(S)

    and assigns them to that key in the result dictionary

    :param res_dict: result dictionary where data is stored
    '''
    pass


def ask_user_input(res_dict: dict[str, Any]) -> None:
    '''Ask the user input via an AppleScript popup window. The user related features are:

        RATING, WATCHED (# times), LAST WATCHED, NOTES

    and assigns them to that key in the result dictionary

    :param res_dict: result dictionary where data is stored

    '''
    pass


def film_data_json(feat_names: list[str], film_id: int, film_title: str) -> str:
    '''Organizes film data fetched into a Python dict, encodes to a JSON object, and returns
    a string of the JSON object

    :param feat_names: Feature names currently in the sc-im spreadsheet
    :param film_id: Unique id for the film
    :param film_title: updated title if user edited it or original title
    :return: str of JSON object
    '''
    # create dict with feature names
    res_dict: dict[str, Any] = {}
    for name in feat_names:
        # since given as param just set immediately
        if name == "FILM":
            res_dict[name] = film_title
        else:
            res_dict[name] = None

    # call functions with dict which will fill their respective keys with values
    get_film_details(res_dict)
    get_film_credits(res_dict)
    get_film_user_input(res_dict)

    return json.dumps(res_dict)

def main():
    # config
    init(autoreset=True)

    # check has feature names and title args
    if len(sys.argv) != 3:
        print(Fore.RED + "Error: too many args")
        sys.exit(1)

    # make a list of feature names
    # removes the last empty string since lua script appends extra comma
    feat_names: list[str] = sys.argv[1][:len(sys.argv[1]) - 1].split(",")
    search_title: str = sys.argv[2].strip()

    film_title, film_id = search_for_film(search_title)

    # send feature names, film indetifier number, and potentially updated title if user edited it
    res: str = film_data_json(feat_names, film_id, film_title)

    return res


if __name__ == "__main__":
    main()

