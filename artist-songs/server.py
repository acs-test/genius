# Extra Project Final for PNE 2018


import http.server
import json
import socketserver
import sys
import urllib

socketserver.TCPServer.allow_reuse_address = True

PORT = 8000

class GeniusHandler(http.server.BaseHTTPRequestHandler):

    api_token = None

    def send_query(self, query):
        """
        Send a query to the Genius API

        :param query: query to be sent
        :return: the result of the query in JSON format
        """

        headers = {'User-Agent': 'http-client'}

        conn = http.client.HTTPSConnection("api.genius.com")

        headers = {"Authorization": "Bearer " + self.api_token}


        print("Sending to Genius the query", query)

        conn.request("GET", query, None, headers)
        r1 = conn.getresponse()
        print(r1.status, r1.reason)
        res_raw = r1.read().decode("utf-8")
        conn.close()

        res = json.loads(res_raw)

        return res

    def fetch_songs(self, artist_name):
        """
        Fetch all songs from an artist given her name


        :param artist_name: name of the artist from which to search the songs
        :return: max list of songs found without pagination
        """

        songs = []

        # First we need to find the artist_id in Genius for artist_name
        artist_id = None
        url = "/search?q=" + artist_name
        res_json = self.send_query(url)
        for item in res_json['response']['hits']:
            artist_found = item['result']['primary_artist']['name']
            if artist_name.replace("+", " ").lower() in artist_found.lower():
                artist_id = item['result']['primary_artist']['id']
                print("Using artist found", item['result']['primary_artist']['name'])
                break

        if not artist_id:
            return songs

        # Only get the songs that can be included in one page
        page = 1
        per_page = 50  # Max number per page

        url = "/artists/%s/songs?per_page=%i&page=%i" % (artist_id, per_page, page)

        songs_res = self.send_query(url)

        # Let's get the title of the songs

        songs = songs_res['response']['songs']

        return songs

    def songs2html(self, songs):
        """
        Convert a list of songs to HTML
        :param songs: list of genius object songs
        :return: an HTML contents with the songs
        """

        html = "<html>"
        html += "<head>"
        html += "<meta charset=\"UTF-8\">"  # Genius API return UTF8 enconding
        html += "<title>List of songs</title>"
        html += "</head>"
        html += "<body>"
        html += "<ul style='list-style: none;' >"
        for song in songs:
            html += "<li style='height:50px'>"
            if 'default_cover' not in song['header_image_thumbnail_url']:
                html += "<img align='left' height='50' width='50' src='" + song['header_image_thumbnail_url'] + "'>"
            html += "<a href='" + song['url'] + "'>"
            html += "<h4>" + song['title'] + "</h4>"
            html += "</a>"
            html += "</li>"
        html += "</ul>"
        html += "</body>"
        html += "</html>"

        return html

    # GET
    def do_GET(self):
        """
        API to be supported

        searchSongs?artist=<name>
        """

        http_response_code = 200
        http_response = "<h1>Not supported</h1>"

        if self.path == "/":
            # Return the HTML form for searching
            with open("artist.html") as file_form:
                form = file_form.read()
                http_response = form
        elif 'searchSongs' in self.path:
            param = self.path.split("?")[1]
            artist_name = param.split("=")[1]
            songs = self.fetch_songs(artist_name)
            if songs:
                http_response = self.songs2html(songs)
            else:
                http_response = "<h1>No songs found for %s</h1>" % artist_name
        else:
            http_response_code = 404

        # Send response status code
        self.send_response(http_response_code)

        # Send extra headers headers

        # Send the normal headers
        self.send_header('Content-type', 'text/html')
        self.end_headers()

        # Write content as utf-8 data
        self.wfile.write(bytes(http_response, "utf8"))
        return


GeniusHandler.api_token = sys.argv[1]

httpd = socketserver.TCPServer(("", PORT), GeniusHandler)
print("serving at port", PORT)
httpd.serve_forever()