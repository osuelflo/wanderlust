from http.server import HTTPServer, BaseHTTPRequestHandler
import psycopg2
from psycopg2 import Error

HOST = "localhost"
PORT = 9999

class MyHTTP(BaseHTTPRequestHandler):

    # Override
    def do_GET(self):   # how should we respond to a GET request
        self.send_response(200)

        self.send_header("Content-type", "application/json")
        self.send_header('Access-Control-Allow-Origin', '*')

        self.end_headers()

        print("ended headers, trying Pg connection")
        try:
            # Connect to an existing database
            connection = psycopg2.connect(user="postgres",
                                        password="Gd1123581321345589!",
                                        host="127.0.0.1",
                                        port="5432",
                                        database="postgres")

            # Create a cursor to perform database operations
            cursor = connection.cursor()
            # Print PostgreSQL details
            print("PostgreSQL server information")
            print(connection.get_dsn_parameters(), "\n")
            # Executing a SQL query
            cursor.execute(""" WITH start AS (
        SELECT topo.source --could also be topo.target
        FROM mn_2po_4pgr as topo
        ORDER BY topo.geom_way <-> ST_SetSRID(
            ST_GeomFromText('POINT (-93.167165 44.936098)'),
        4326)
        LIMIT 1
        ),
        -- find the nearest vertex to the destination longitude/latitude
        destination AS (
        SELECT topo.target --could also be topo.target
        FROM mn_2po_4pgr as topo
        ORDER BY topo.geom_way <-> ST_SetSRID(
            ST_GeomFromText('POINT (-90.337104 47.751911)'),
        4326)
        LIMIT 1
        )
        -- use Dijsktra and join with the geometries
        SELECT ST_AsText(ST_LineMerge(ST_AsText(ST_Transform(ST_Union(geom_way), 4326)))) as route
        FROM pgr_dijkstra('
            SELECT id,
                source,
                target,
                ST_Length(ST_Transform(geom_way, 3857)) AS cost
                FROM mn_2po_4pgr',
            array(SELECT source FROM start),
            array(SELECT target FROM destination),
            directed := false) AS di
        JOIN   mn_2po_4pgr AS pt
        ON   di.edge = pt.id;""")
            # Fetch result
            record = cursor.fetchone()
            print("You are connected to - ", record, "record \n")

        except (Exception, Error) as error:
            print("Error while connecting to PostgreSQL", error)
        finally:
            if (connection):
                cursor.close()
                connection.close()
                print("PostgreSQL connection is closed")
        
        self.wfile.write(bytes("{}".format(record), "utf-8"))


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
