"""Module for printing ascii introduction."""
from termcolor import colored
from pyfiglet import figlet_format


def print_ascii():
    """Function to print ascii introduction."""
    result = colored(figlet_format("Welcome! \n This is Collectington"), color="green")

    print(result)
