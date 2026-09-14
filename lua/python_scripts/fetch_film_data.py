'''
Fetch data from the tmdb3 database for a specified film or list of films

@author Garret Wilson
'''


import os
import sys
import subprocess

from dotenv import load_dotenv
from colorama import init, Fore, Style
from tmdbv3api import TMDb, Movie
from tmdbv3api.tmdb import AsObj


def get_user_input(opts: list[str]) -> int:
    '''Spawns an input window that list the film options a user can choose between

    :param opts: list of movie titles and release date
    :return: index (by 1) of movie chosen by user
    '''

    # format the options for the AppleScript
    applescript_list = "{" + ', '.join(opts) + "}"

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


def ask_title_change(search: AsObj, index: int) -> None:
    '''Spawns an input window that asks the user if they want to change the film title

    :param search: tmdb object 
    :param index: index of movie title chosen
    '''

    # allow user to edit title
    curr_title = search[index].title
    prompt: str = f"Change film title? (current title: '{Fore.YELLOW + Style.BRIGHT + curr_title + Style.RESET_ALL + Fore.RESET}') [Y / N]: "
    res = input(prompt)
    while True:
        if res != "Y" and res != "y" and res != "N" and res != "n":
            res = input(prompt)
            continue
        break

    if res == "Y" or res == "y":
        new_title = input("New title: ")
        confirmation = input(f'Confirm new title: "{Fore.YELLOW + Style.BRIGHT + new_title + Style.RESET_ALL + Fore.RESET}"? [Y / N]: ')
        while True:
            if confirmation == "N" or confirmation == "n":
                new_title = input("New title: ")
                confirmation = input(f'Confirm new title: "{Fore.YELLOW + Style.BRIGHT + new_title + Style.RESET_ALL + Fore.RESET}"? [Y / N]: ')
                continue
            break

        search[index].title = new_title


def main():
    # config
    init(autoreset=True)
    load_dotenv()
    tmdb = TMDb()
    tmdb.api_key = os.getenv("API_KEY")
    tmdb.language = "en"
    movie = Movie()

    # check just title given
    if len(sys.argv) > 2:
        print(Fore.RED + "Error: too many args")
        sys.exit(1)

    search_title: str = sys.argv[1]
    search: AsObj = movie.search(search_title)

    # if more than one result, allow user to choose film
    if len(search) > 1:
        count: int = 0

        # build AppleScript list
        opts: list[str] = []
        for m in search:
            opts.append(f'"[{count+1}] {m.title} ({m.release_date})"')
            count += 1

        # index in pop up window is by 1, so need to 0 index
        index: int = get_user_input(opts) - 1

        ask_title_change(search, index)

        print(search[index])

    else:
        print(search[0])


if __name__ == "__main__":
    main()

