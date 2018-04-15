import requests
import re
import sys
from datetime import datetime
from bs4 import BeautifulSoup
import urllib

def title_case(string):
    string = string.lower()
    toupper = lambda m: m.group(1).upper()
    string = re.sub( r'\b([a-z])', toupper, string )
    return string

class Event():
    def __init__(self):
        self.artist = None
        self.venue = None
        self.date = None
        self.tickets = ""
        self.price = ""
        self.type = ""
        self.misc = []

    def __str__(self):
        string = self.date.strftime("%d-%b-%Y (%a)").ljust(20)
        if self.artist:
            string += self.artist
        if self.venue:
            string += "\n" + (" " * 20) + self.venue
        if self.price:
            string += "\n" + (" " * 20) + self.price
        if self.tickets:
            string += "\n" + (" " * 20) + self.tickets
        # if self.misc:
        #     for m in self.misc:
        #         string += "\n        %s" % m
        return string

class GreenMind():
    def __init__(self):
        self.events = []
        base_url = r'http://www.wegottickets.com/greenmind/searchresults/page/'
        index = 1

        print("Parsing page ", end="")
        while True:
            print(index, end="")
            sys.stdout.flush()
            url = base_url + str(index) + '/all#paginate'
            page_events = self.parse_page(url)
            self.events += page_events
            if not page_events:
                break
            index += 1

    def parse_page(self, url):
        r = requests.get(url)
        soup = BeautifulSoup(r.text, 'lxml')

        divs0 = soup.findAll( "div", {"class": "content block-group chatterbox-margin padded listing"} )
        divs1 = soup.findAll( "a", {"class": "event_link"} )
        divs2 = soup.findAll( "div", {"class": "venue-details"} )

        #print( "%d %d subdivs" % ( len(divs1), len(divs2) ) )

        events = []
        for div0, div1, div2 in zip(divs0, divs1, divs2):
            event = self.parse_div(div0, div1, div2)
            events.append(event)

        return events

    def parse_div(self, div0, artist_link, venue_details):
        event = Event()
        div0 = str(div0)
        artist_link = str(artist_link)
        venue_details = str(venue_details)

        m_artist = re.search( '<a[^>]+>([^<]*)</a>', artist_link )
        if m_artist:
            event.artist = title_case( m_artist.group(1) )

        m_venue = re.search( '<h4>\s*CAMBRIDGE\s*:?\s*([^<]+)</h4>', venue_details )
        if m_venue:
            event.venue = m_venue.group(1).strip()

        m_date = re.search( '(\d+).. ([A-Z][a-z][a-z]), (\d\d\d\d)', venue_details )
        if m_date:
            event.date = datetime.strptime( " ".join(m_date.groups()), "%d %b %Y" )

        if "tickets are available" in div0.lower():
            event.tickets = "Tickets are available"
        elif "sold out" in div0.lower():
            event.tickets = "Sold out"
        elif "tickets on sale from" in div0.lower():
            event.tickets = "Not yet on sale"
        else:
            m_tickets = re.search( '(\d+ tickets available)', div0.lower() )
            if m_tickets:
                event.tickets = m_tickets.group(1)

        m_price = re.search( 'class="searchResultsPrice">([^<]+)', div0 )
        if m_price:
            event.price = m_price.group(1).strip()
            if event.price.endswith("="):
                event.price = event.price[:-1]
            event.price = event.price.lower().strip()

        return event

    def get_events(self, pattern=None):
        if pattern:
            matches = []
            for e in self.events:
                if pattern in str(e):
                    matches.append(e)
            return matches
        return self.events

class RoystonFolk():
    def __init__(self):
        self.url = r'http://www.roystonfolk.org/diary/'
        self.events = []
        self.parse_page(self.url)

    def parse_page(self, url):
        headers = {"User-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.80 Safari/537.36"}
        r = requests.get(url, headers=headers)

        current = None

        for line in r.text.split("\n"):
            line = line.strip()
            line = re.sub( "<[^>]+>", "", line )
            if not line:
                continue
            # date_format: Friday 30th March 2018
            m_date = re.search('(\d+)[a-z]{2}\s+([A-Z][a-z]+)\s+(\d{4})', line)
            if m_date:
                day   = m_date.group(1)
                month = m_date.group(2)[0:3]
                year  = m_date.group(3)

                date = datetime.strptime( " ".join([day,month,year]), "%d %b %Y" )

                if not date or date.toordinal() < datetime.now().toordinal():
                    continue

                if current:
                    current.artist = current.misc[2].decode("utf-8").strip()
                    self.events.append(current)
                current = Event()

                current.date = date.date()

                if line.lower().startswith("showcase"):
                    current.type = "Showcase"
                elif line.lower().startswith("concert"):
                    current.type = "Concert"
                else:
                    current.type = "Misc"

            elif current:
                current.misc.append(line.encode("utf-8"))

    def get_events(self, pattern=None):
        if pattern:
            matches = []
            for e in self.events:
                if pattern in str(e):
                    matches.append(e)
            return matches
        return self.events

if __name__ == "__main__":
    pattern = None
    args = sys.argv[1:]
    if len(args) > 0:
        pattern = args[0]

    gm = GreenMind()
    # gm = RoystonFolk()

    for event in gm.get_events(pattern):
        print("\n\n" + str(event))

