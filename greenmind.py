import requests
import re
import sys
from datetime import datetime
from bs4 import BeautifulSoup

class Event():
    def __init__(self, div0, div1, div2):
        self.artist = None
        self.venue = None
        self.date = None
        self.tickets = ""
        self.price = ""
        self.parse_div(div0, div1, div2)

    def parse_div(self, div0, artist_link, venue_details):
        div0 = str(div0)
        artist_link = str(artist_link)
        venue_details = str(venue_details)

        m_artist = re.search( '<a[^>]+>([^<]*)</a>', artist_link )
        if m_artist:
            self.artist = self.title_case( m_artist.group(1) )

        m_venue = re.search( '<h4>\s*CAMBRIDGE\s*:?\s*([^<]+)</h4>', venue_details )
        if m_venue:
            self.venue = m_venue.group(1).strip()

        m_date = re.search( '(\d+).. ([A-Z][a-z][a-z]), (\d\d\d\d)', venue_details )
        if m_date:
            self.date = datetime.strptime( " ".join(m_date.groups()), "%d %b %Y" )

        if "tickets are available" in div0.lower():
            self.tickets = "Tickets are available"
        elif "sold out" in div0.lower():
            self.tickets = "Sold out"
        elif "tickets on sale from" in div0.lower():
            self.tickets = "Not yet on sale"
        else:
            m_tickets = re.search( '(\d+ tickets available)', div0.lower() )
            if m_tickets:
                self.tickets = m_tickets.group(1)

        m_price = re.search( 'class="searchResultsPrice">([^<]+)', div0 )
        if m_price:
            self.price = m_price.group(1).strip()
            if self.price.endswith("="):
                self.price = self.price[:-1]
            self.price = self.price.lower().strip()

    def title_case(self, string):
        string = string.lower()
        toupper = lambda m: m.group(1).upper()
        string = re.sub( r'\b([a-z])', toupper, string )
        return string

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
            event = Event(div0, div1, div2)
            events.append(event)

        return events

    def __str__(self):
        string = ""
        for event in self.events:
            string += "\n\n" + str(event)
        return string

if __name__ == "__main__":
    gm = GreenMind()
    print(gm)

