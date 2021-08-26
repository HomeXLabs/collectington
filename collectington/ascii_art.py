from termcolor import colored
from pyfiglet import figlet_format

def print_ascii():
    result = colored(figlet_format("Welcome! \n This is Collectington"), color="green")

    print(result)