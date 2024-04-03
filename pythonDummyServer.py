from http.server import HTTPServer, BaseHTTPRequestHandler
import psycopg2
from psycopg2 import Error
from urllib.parse import urlparse, parse_qs


"""
Use this server for testing purposes, if you don't have PostgreSQL set up. 
It will always return the coordinates for a route from Macalester College to St. Thomas.
"""

HOST = "localhost"
PORT = 9999

class MyHTTP(BaseHTTPRequestHandler):

    # Override
    def do_GET(self):   # how should we respond to a GET request
        self.send_response(200)

        self.send_header("Content-type", "application/json")
        self.send_header('Access-Control-Allow-Origin', '*')

        self.end_headers()

        # checks the GET request for extra parameters and stuff
        urlData = urlparse(self.path, allow_fragments = False)

        # creates some variables for the start & end coordinates we passed it from the JS
        # we later use these variables as part of a string formatting in the SQL request to set the beginning and end coords of our route
            # The parse_qs command just checks the urlData object for the specific segment of parameters we want to look at
                # then it checks the specific name of each parameter and grabs the first thing in that slot. I bet the [0] can be deleted
        record = "('LINESTRING(-93.1880424 44.9472681,-93.1874836 44.9472674,-93.1873656 44.9472672,-93.185732 44.947262,-93.184163 44.947255,-93.1840731 44.9472546,-93.182721 44.947248,-93.180729 44.947239,-93.178544 44.947229,-93.1771997 44.947222,-93.1771999 44.9469785,-93.1771333 44.9469702,-93.1770734 44.9469551,-93.176958 44.9469468,-93.1769025 44.9469462,-93.1768533 44.9469348,-93.1767185 44.9468706,-93.1766183 44.9468423,-93.1765916 44.9467289,-93.17659 44.9465489,-93.174653 44.9465551,-93.174656 44.945754,-93.174659 44.945036,-93.174661 44.9445116,-93.174663 44.943972,-93.1746655 44.943443,-93.174668 44.942923,-93.1746595 44.9423656,-93.1745566 44.9423443,-93.1745695 44.9417524,-93.1745659 44.9417047,-93.1745315 44.9416439,-93.1744902 44.9415758,-93.1744449 44.9414954,-93.1742101 44.9414171,-93.1740992 44.9413973,-93.1738966 44.9413827,-93.1722188 44.9413746,-93.1710315 44.9413689,-93.170468 44.9413662,-93.1704681 44.9412879,-93.1695698 44.9412826,-93.1695695 44.9412389,-93.1694772 44.9412339,-93.169479 44.9408839,-93.1694788 44.940801,-93.1694777 44.9404482,-93.1694791 44.9401946,-93.1694791 44.9401611,-93.169479 44.9400814,-93.1694774 44.9400245,-93.1694736 44.939992,-93.1694138 44.9399636,-93.169043 44.9396958,-93.168804 44.9394485,-93.1686692 44.9394496,-93.1680758 44.9394457,-93.1680701 44.9394261,-93.1680587 44.9393873,-93.1680178 44.9393243,-93.1679536 44.9392659,-93.167911 44.9392507,-93.1678669 44.939235,-93.1678693 44.9389253,-93.1678765 44.9388985,-93.1678155 44.9388696,-93.1677951 44.9385122,-93.1677933 44.9383404,-93.1677911 44.938122,-93.1674829 44.9381205,-93.1672037 44.9381208,-93.167201 44.9378693,-93.1672019 44.9369408,-93.1670988 44.9369408,-93.1671001 44.936108,-93.1671009 44.936026,-93.1670938 44.9356318,-93.1670953 44.9352565,-93.1669669 44.9352564,-93.166967 44.9351802)',)"

        # THIS IS THE LINE THAT DOES THE HTTP RESPONSE - we just return the results we get from our SQL query
        self.wfile.write(bytes("{}".format(record), "utf-8"))


    # I needed to add this because chrome tries to do some logic about whether we're allowed to add parameters to our GET request
        # I think chrome first checks our options to see if the request is legal, and then actually runs the GET request
        # apparently as part of that built in process, we need to set this Access-Control-Allow-Origin shit
    def do_OPTIONS(self):
        
        self.send_response(200) # 200 is a successful response

        # Set the Access-Control-Allow-Origin header to allow requests from all origins
        self.send_header('Access-Control-Allow-Origin', '*')

        # Set the Access-Control-Allow-Methods header to allow specific methods
        self.send_header('Access-Control-Allow-Methods', 'GET')

        # Set the Access-Control-Allow-Headers header to allow specific headers
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

        # End the headers section
        self.end_headers()



server = HTTPServer((HOST, PORT), MyHTTP)
print("Server now running...")
server.serve_forever()
