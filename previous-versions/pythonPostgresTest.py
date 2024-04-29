import psycopg2
from psycopg2 import Error


try:
    # Connect to an existing database
    connection = psycopg2.connect(user="postgres",
                                password="YOUR_POSTGRES_PASSWORD",
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
  FROM minnesota_2po_4pgr as topo
  ORDER BY topo.geom_way <-> ST_SetSRID(
    ST_GeomFromText('POINT (-93.167165 44.936098)'),
  4326)
  LIMIT 1
),
-- find the nearest vertex to the destination longitude/latitude
destination AS (
  SELECT topo.target --could also be topo.target
  FROM minnesota_2po_4pgr as topo
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
        FROM minnesota_2po_4pgr',
    array(SELECT source FROM start),
    array(SELECT target FROM destination),
    directed := false) AS di
JOIN   minnesota_2po_4pgr AS pt
  ON   di.edge = pt.id;""")
    # Fetch result
    record = cursor.fetchone()
    print("You are connected to - ", record, "\n")

except (Exception, Error) as error:
    print("Error while connecting to PostgreSQL", error)
finally:
    if (connection):
        cursor.close()
        connection.close()
        print("PostgreSQL connection is closed")