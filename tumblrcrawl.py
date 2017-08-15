#!/usr/bin/python

'''
    tumblrcrawl.py - download images and video from tumblr sites
    Copyright (C) 2017 Mark Whittaker

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

'''

import sys
import os
import urllib.request
import urllib.error
import xmltodict
import datetime
import datedelta
import subprocess

# Container to hold filenames
FILELIST = []

# Number of posts to retrieve on each call to Tumblr (default is 20, max is 50)
NUMBER = 50

def add_to_list(xmldata, beginning):
    # Are we prior to our end date
    flag = True
    
    # Reply now a dictionary. Look down into <Post> fot the date tag
    try:
        for posts in xmldata['tumblr']['posts']['post']:
            date_of_post = posts['@date-gmt'].split()[0]
            
            if date_of_post > beginning:
                #print(beginning, date_of_post)
                try:
                    #photo_num = len(posts['photoset']['photo'])
                    #for i in range(0, photo_num):
                    for sets in posts['photoset']['photo']:
                        FILELIST.append(sets['photo-url'][0]['#text'])
                        #FILELIST.append(posts['photoset']['photo'][i]['photo-url'][0]['#text'])
                except:
                    FILELIST.append(posts['photo-url'][0]['#text'])
            else:
                flag = False
    except:
        flag = False
    
    return flag

def generate_photo_list(NUMBER):
    backdate = 0
    proceed = True
    offset = 0
    counter = 0
    
    # How far back (in months) to go. 0 is no limit.
    if len(sys.argv) == 3:
        backdate = int(sys.argv[2])
    
    # Only crawl last number of months
    if backdate > 0:
        d = datetime.datetime.today()
        r = d - datedelta.datedelta(months=int(backdate))
        beginning = r.strftime("%Y-%m-%d")
    else:
        beginning = "2012-01-01"
    
    while proceed:
        counter += 1
        print("Getting Page " + str(counter))
        # Get site info from Tumblr
        tumblr_url = "http://{0}.tumblr.com/api/read?type=photo&num={1}&start={2}"
        site_url = tumblr_url.format(sys.argv[1], NUMBER, offset)
        
        try:
            response = urllib.request.urlopen(site_url)
        except urllib.error.URLError as e:
            sys.stderr.write(e.reason + '\n')
            sys.exit(1)
        
        data = xmltodict.parse(response.read())
        proceed = add_to_list(data, beginning)
        offset += NUMBER
    
    
def start_aria_job():
    # Not interested in GIFs
    newlist = [ x for x in FILELIST if x.find(".gif") == -1]
    # Remove duplicates
    newlist = list(set(newlist))
    
    # Write a manifest for aria2c
    with open("manifest", 'w') as f:
        for s in newlist:
            f.write(s + '\n')
    
    # Run aria2c to do the work
    subprocess.call(["aria2c", "-j4", "-i", "manifest", "-s1", "-c", "-d", sys.argv[1]])
    
    # Cleanup
    os.remove("manifest")


if __name__ == "__main__":
    sites = None
    
    if len(sys.argv) < 2:
        sys.stderr.write("I need a tumblr name to crawl\n")
    
    generate_photo_list(NUMBER);
    print("Total posts " + str(len(FILELIST)))
    start_aria_job()
