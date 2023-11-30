#! python

# This script will update or install all basic CALDB instrument files.
# Python 3.10+ is likely required due to type hints.

import os
import re
import subprocess
import urllib.error
import urllib.parse
import urllib.request


def open_website(url: str, timeout: int = 90,
                 split: bool = True, verbose: bool = True) -> list | str | None:
    """
    Open a website and return the contents.

    Parameters
    ----------
    url : str
        The URL to open.
    timeout : int
        The timeout in seconds.
    split : bool, default True
        Split the contents into a list of lines. If false, return the complete contents.
    verbose : bool, default True
        Print the URL to the screen.

    Returns
    -------
    list | str | None
        The contents of the website.

    """
    try:
        if verbose:
            print(f"Loading {url}")
        with urllib.request.urlopen(url, timeout=timeout) as website:
            encoding = website.info().get_param('charset', 'utf8')
            html = website.read().decode(encoding)
            if split:
                return html.splitlines()
            else:
                return html

    except urllib.error.HTTPError as e:
        print("Cannot retrieve URL: HTTP Error Code {0}".format(e.code))
        return None

    except urllib.error.URLError as e:
        print("Could not access the URL {0}".format(e))
        return None

    except:
        print("Unknown problem accessing URL.")
        return None



def get_telescope_links() -> dict:
    """
    This function will get the links to the telescope files
    
    Parameter
    ---------
    None

    Returns

    """

    url = ('https://heasarc.gsfc.nasa.gov/docs/heasarc/caldb/'
           'caldb_supported_missions.html')
    lines = open_website(url)

    # Exit if the website didn't loat
    if lines is None:
        return None

    links = dict()
    for line in lines:
        if re.search('(A|a).*(HREF|href)=.*(T|t)ar file', line):
            compressed_url = re.search('(HREF|href)="(.*)"', line).group(2)
            if '"' in compressed_url:
                compressed_url = compressed_url.split('"')[0]
            _, mission, telescope, file_name = compressed_url.rsplit('/', 3)
            links[(mission, telescope)] = compressed_url

    return links


def download_files():
    """
    This function will download the files from the links
    """

    caldb_dir = os.getenv('CALDB', None)
    if caldb_dir is None:
        print("CALDB environment variable not set. Exiting.")
        return None

    # Move to the CALDB directory
    os.chdir(caldb_dir)

    links = get_telescope_links()

    # Download the files
    for key, link in links.items():
        if not os.path.exists(link.split('/')[-1]):
            try:
                print(f"Downloading {key[0]} {key[1]}")
                urllib.request.urlretrieve(link, link.split('/')[-1])

                print(f"Unpacking {key[0]} {key[1]}")
                subprocess.run(['tar', '-xzf', link.split('/')[-1]])
            except:
                print('Problem downloading file.')

    # Initialize the instruments in CALDB
    for key, link in links.items():

        if key[0]=='data':
            continue

        print(f"Initializing {key[0]} {key[1]}")
        p = subprocess.run(['caldbinfo', 'INST',
                            key[0].upper(), key[1].upper()], capture_output=True)
        print(p.stdout.decode('utf-8'))
        if re.search('ERROR', p.stdout.decode('utf-8')):
           print(f"Problem downloading {link.split('/')[-1]}")


if __name__ == '__main__':
    download_files()
