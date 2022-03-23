"""
    khinsider_downloader

    Downloads full albums, album art, and other information from video game
    soundtracks hosted on khinsider.

    Copyright (C) 2019 Edward Salkield
    edward.salkield@gmail.com

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""


import sys, os
import requests
import argparse
import re
from bs4 import BeautifulSoup


# Constants
DL_SERVER = "https://downloads.khinsider.com"
quiet = False


# Functions
#  print quietly
def qprint(msg):
    if not quiet:
        print(msg)

#  save file at url to path
def save(url, name, path):
    try:
        response = requests.get(url)
    except Exception:
        qprint("\t" + "ERROR: Could not save " + name + " at URL: " + url)
        return 1

    with open(path, 'wb') as f:
        f.write(response.content)
        qprint("\t" + name + " saved!")
    
    return 0


def main():

    # Define command line parameters
    parser = argparse.ArgumentParser(description="Download albums from khinsider.com")
    parser.add_argument("source_url")
    parser.add_argument("destination_path")
    parser.add_argument("--quality", help="The file extension quality to download", default=".mp3")
    parser.add_argument("--info", help="Name of album info file to download", default="info.txt")
    parser.add_argument("--noart", help="Don't download album art", action="store_true")
    parser.add_argument("--noinfo", help="Don't download info", action="store_true")
    parser.add_argument("--nomusic", help="don't download music", action="store_true")
    parser.add_argument("--countfrom1", help="Count track numbers from 1 instead of 0", action="store_true")
    parser.add_argument("-q", help="Run in quiet mode", action="store_true")


    args = parser.parse_args()
    url = args.source_url
    path = args.destination_path
    quality = args.quality
    info_name = args.info
    quiet = args.q


    # Test input sanity
    if not os.path.isdir(path):
        print("destination_path is not a directory. Creating...")
        os.mkdir(path)

    if path[-1] != '/':
        path = path + '/'

    if not '.' == quality[0]:
        quality = "." + quality

    # Get the page data
    response = requests.get(url)
    success = response.content
    page = response.text
    soup = BeautifulSoup(page, 'html.parser')
    qprint("Successfully parsed page data")


    # Save album information
    if not args.noinfo:
        albuminfo = ""
        for p in soup.find_all('p'):
            text = p.get_text()
            if "Album name" in text:
                # Format correctly
                
                albuminfo = re.sub(r"\t", "", text.strip())

        with open(path + info_name, 'w') as f:
            if albuminfo == "":
                print("ERROR: Could not locate file info at the given url. Is the link to a valid khinsider page?")
                sys.exit()
            
            qprint("Saving album info...")
            f.write(albuminfo)
            qprint("Saved!")
     

    # Save album art
    if not args.noart:
        qprint("Saving album art...")
        images = []

        for p in soup.find_all("table"):
            imgs = p.find_all("img")
            if imgs != []:
                images = imgs
                
        if images == []:
            print("ERROR: Could not find album art for this album! Continuing...")

        img_urls = [i["src"] for i in images]
        img_names = [i.split("/")[-1] for i in img_urls]

        for (url, name) in zip(img_urls, img_names):
            save(url, name, path + name)

    # Save music
    if not args.nomusic:
        qprint("Saving music...")
        track_names = []
        track_urls = []

        songlist = soup.find("table", {"id": "songlist"})
        for t in songlist.find_all("tr"):
            try:
                if t["id"] in ["songlist_header", "songlist_footer"]:
                    continue
            except KeyError:
                pass

            cell = t.find("td", {"class": "clickable-row"})
            if cell is None:
                # TODO: proper debug output
                print("Error: cell is None")
                print(t)
            else:
                name = cell.a.text + quality
                track_names.append(cell.a.text + quality)
                track_urls.append(cell.a["href"])

        if track_names == []:
            print("ERROR: Could not find music for this album! Exiting...")
            sys.exit()

        track_names = [str(n+int(args.countfrom1)).zfill(2) + " - " + name
                        for n,name in enumerate(track_names)]
        track_urls = [DL_SERVER + ".".join(t.split(".")[:-1]) + quality for t in track_urls]

        for (url, name) in zip(track_urls, track_names):
            songpage  = BeautifulSoup(requests.get(url).text, "html.parser")
            for span in songpage.find_all("span", {"class": "songDownloadLink"}):
                if quality in span.parent["href"]:
                    song_url = span.parent["href"]
                else:
                    # TODO: debug output
                    pass

            print(url)
            save(song_url, name, path + name)

    print("Download completed!")

if __name__ == "__main__":
    main()
