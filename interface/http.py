from lxml.etree import HTML
from os.path import join
from re import compile
from urllib.request import urlopen, urlretrieve
from urllib.parse import urljoin
from .filesystem import find_targets_downloaded


def get_xml_page(url):
    """Opens url with urllib and returns xml of downloaded page

    :param url: Text server url to open
    :return: lxml.etree xml object of HTML-page
    """
    servers = {}

    # Get and read the text from the webpage
    with urlopen(url) as webpage:
        page = webpage.read()

    xml = HTML(page)

    return xml


def download_targets(targets, destination, verbose=False):
    """Download files specified target by target

    :param targets: Nested dictionary with target identifiers as keys, and
                    dictionary as values. Value dictionary has filenames as keys
                    and downloadable URL's as values
    :param destination: text path to directory in where to save downloads
    :param verbose: boolean, print download actions if true
    :return: Nested dictionary with target id as keys, dictionary as values.
             Value dictionary with filenames as keys and local path to files
             as values.
    """
    downloaded = {}
    for target in targets:
        downloads = {}
        for target_file in targets[target]:
            download_path = join(destination, target_file)
            if verbose:
                print("\t".join(["Downloading", target, "from", target_file, "->", download_path ]))
            urlretrieve(targets[target][target_file], download_path)
            downloads[target_file] = download_path
        downloaded[target] = downloads

    return downloaded


def download_new_targets(url, destination, targetregex="^(T.\d+)[-.]"):
    """Download new files from a standard APACHE listing (predictioncenter.org)

    :param url: text url where APACHE listing is available
    :param destination: text path do directory where to store downloaded files
    :return: Nested dictionary with downloaded targets and their files
             1) text target ID as keys, dictionaries as values
             2) text filesnames as keys, text pathnames as values
    """
    # Fix url so that urljoin won't fail
    if url[-1] != '/':
        url += '/'
    # List files already downloaded
    downloaded = find_targets_downloaded(destination)
    # Read page
    xml = get_xml_page(url)
    # Find all downloadables
    target = compile(targetregex)
    # Dictionary with downloaded files
    # Target -> filename > path
    # Store path from downloaded
    targets_downloaded = {}
    # Dictionary with files to be downloaded
    # Target -> filename > url
    # Store path from downloaded to here
    to_download = {}
    for element in xml.xpath("//tr//td//a"):
        m = target.match(element.text)
        if m:
            targetname = m.group(1)
            targeturl = element.get("href")
            # Only download new files, not already downloaded
            if targeturl not in downloaded:
                if targetname not in to_download:
                    to_download[targetname] = {}
                # Save download target -> filename -> url
                to_download[targetname][targeturl] = urljoin(url, targeturl)
            else:
                if targetname not in targets_downloaded:
                    targets_downloaded[targetname] = {}
                # Save target -> filename -> path
                targets_downloaded[targetname][targeturl] = downloaded(targeturl)

    # Download all new files
    new_downloaded = download_targets(to_download, destination)

    # Update downloaded dictionary
    for target in new_downloaded:
        if target not in targets_downloaded:
            targets_downloaded[target] = {}
        for target_file in new_downloaded[target]:
            targets_downloaded[target][target_file] = new_downloaded[target][target_file]

    return targets_downloaded