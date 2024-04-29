from http.server import HTTPServer, BaseHTTPRequestHandler
import psycopg2
from psycopg2 import Error
from urllib.parse import urlparse, parse_qs


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
        start = parse_qs(urlData.query)["start"][0]
        destination = parse_qs(urlData.query)["destination"][0]
        weight = parse_qs(urlData.query)["weight"][0]


        print("start", start, "destination", destination, "weight", weight)

        # run the python code we want to run after performing a GET request on this
        try:
            # Connect to an existing database
            connection = psycopg2.connect(user="postgres",
                                        password="password",
                                        host="localhost",
                                        port="5432",
                                        database="postgres")

            # Create a cursor to perform database operations
            cursor = connection.cursor()


            # Print PostgreSQL details
            # print("PostgreSQL server information")
            # print(connection.get_dsn_parameters(), "\n")
            
            # This is our pgrouting query!! I think .execute actually runs a query
            cursor.execute(""" WITH start AS (
        SELECT topo.source --could also be topo.target
        FROM minnesota_2po_4pgr as topo
        ORDER BY topo.geom_way <-> ST_SetSRID(
            ST_GeomFromText('POINT ({start})'),
        4326)
        LIMIT 1
        ),
        -- find the nearest vertex to the destination longitude/latitude
        destination AS (
        SELECT topo.target --could also be topo.target
        FROM minnesota_2po_4pgr as topo
        ORDER BY topo.geom_way <-> ST_SetSRID(
            ST_GeomFromText('POINT ({destination})'),
        4326)
        LIMIT 1
        )
        -- use Dijsktra and join with the geometries
        SELECT ST_AsText(ST_LineMerge(ST_AsText(ST_Transform(ST_Union(geom_way), 4326)))) as route
        FROM pgr_dijkstra('
            SELECT id,
                source,
                target,
                {weight} AS cost, reverse_cost
                FROM minnesota_2po_4pgr',
            array(SELECT source FROM start),
            array(SELECT target FROM destination),
            directed := true) AS di
        JOIN   minnesota_2po_4pgr AS pt
        ON   di.edge = pt.id;""".format(start = start, destination = destination, weight = weight))
            
            # This saves the result of the executed query somewhere
            record = cursor.fetchone()

            #print("You are connected to - ", record, "\n")

        except (Exception, Error) as error:
            print("Error while connecting to PostgreSQL", error)

        finally:    # close our connection to Postgres after we make our request
            if (connection):
                cursor.close()
                connection.close()
                print("PostgreSQL connection is closed")
        
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
