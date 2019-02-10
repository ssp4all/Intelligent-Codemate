# This file will extract error from file passed as extension
import os
import re
import sys

from funtions import run, runrealtime, toString
from install_packages import install
from scrape import get_search_results
from terminal import get_terminal_size

# ASCII color codes
GREEN = '\033[92m'
GRAY = '\033[90m'
CYAN = '\033[36m'
RED = '\033[31m'
YELLOW = '\033[33m'
END = '\033[0m'
UNDERLINE = '\033[4m'
BOLD = '\033[1m'

########################################
# Get file type by knowing its extension
########################################


def get_language(file_path):
    if file_path.endswith(".py"):
        return "python3"
    elif file_path.endswith(".js"):
        return "node"
    elif file_path.endswith(".go"):
        return "go run"
    elif file_path.endswith(".rb"):
        return "ruby"
    elif file_path.endswith(".class"):
        return "java"
    else:
        return ' '  # Unknown filetype


########################################
# Extract error
########################################
def get_error_message(file):
    if get_language(file) == 'python3':
        print("Checking for the error in the "+file+"...")
        output, error = runrealtime(
            ["python", os.path.join(sys.path[0], file)])
        if len(error) == 0:
            print('Done, Good to GO!')
        else:
            err = toString(error)
            er = re.search('\n(?:[ ]+.*\n)*(\w+: .*)', err).groups()
            error = er[0]  # To get first element of tuple consists of errors
            # print(value)
            print('#'*sizex)
            print(error)
            print('#'*sizex)
            print('Error...Unable to run file!')
            # sys.exit()

        c = input('Do you want to seach web(y/n) :')
        if c == 'y':
            get_search_results(error)
        else:
            print('Exiting....')
            exit(1)
    else:
        print('Only Python is supported...Exiting')
        exit(1)


def print_help():
    print('Help --> %sIntelligent-Codemate%s\n' % (BOLD, END))
    print('WELCOME')
    print()
    print('1]   python codemate.py -q what is web-scraping')
    print()
    print('2]   python codemate.py your_file.py')
    print()
    print('3]   python codemate.py')


########################################
# Accept file
########################################

def main():
    # Get terminal size
    sizex, sizey = get_terminal_size()

    if len(sys.argv) == 1 or sys.argv[1].lower() == '-h':
        print_help()
    elif sys.argv[1].lower() == '-q' or sys.argv[1].lower() == '--query':
        query = ' '.join(sys.argv[2:])

        print()
        print('#'*sizex, end='')  # find current teminal width
        print(query.upper())
        print('#'*sizex)
        print()
        # while True:
        get_search_results(query)
        # print('Do you want to EXIT press ctrl+C')
        # search_results, captcha = seach_stackoverflow(query)

        # if search_results != []:
        #     if captcha:
        #         sys.stdout.write("\n Sorry, Try again Later")
        #         return
        #     else:
        #         return #currently Do nothing
    else:
        language = get_language(sys.argv[1].lower())
        print(language)
        if language == ' ':
            sys.stdout.write("\nSorry, Unknown File type...")
        get_error_message(sys.argv[1].lower())


if __name__ == "__main__":
    main()
