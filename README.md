# wanderlust
## Installation Process
### Step 1:  Installing PostgreSQL and PostGIS

Install PostgreSQL from [This Link](https://www.enterprisedb.com/downloads/postgres-postgresql-downloads).
Follow the prompts, pay attention to the server details (Listening port, etc.), then once finished check the box to launch stack builder.  
Follow prompts once more until the option to add spatial extensions appears, under which we checked the box for PostGIS. Once this is complete, pgAdmin can be opened and used to create a database, and `CREATE EXTENSION postgis;` can be used to add the extension.
This was all done according to [this tutorial](https://mapscaping.com/getting-started-with-postgis/).

### Step 2:  Converting OSM Data to Data for PGRouting

PGRouting needs a certain data structure in order to operate, and raw OSM files have to be passed through two conversion programs.  The first step is to convert an OSM data file to one that PSQL can handle using osm2pgsql, which can be ofund [here](https://osm2pgsql.org/doc/install.html).  Then, the path to the directory containing the osm2pgsql executable file must be added to the path environment variables (within the System Envirment variables section), added in the "Edit System Environment Variables" menu.  The next step is to get an OSM file, we did this using [geofabrik](https://www.geofabrik.de/) in the pbf format.  The default style must also be downloaded, here is a [link](https://learnosm.org/files/default.style).  Once all these steps are complete, this command `osm2pgsql -c -d postgres -U postgres -H localhost -r pbf -W -S C:\osm2pgsql_guide\default.style C:\osm2pgsql_guide\Lisbon.osm.pbf`  The paths should be replaced with your own, and the database should be whatever you named it.  The data should now exist in PGAdmin in your database.  

We have one more conversion to do to get it to become data that can be used by pgRouting.  Download [osm2po](https://osm2po.de/), unzip the folder, then open the config file. Change line 190 to “wtr.finalMask = car,foot,bike”. This will filter the OSM data to segments with these tags, then Uncomment (remove the “#” at the beginning) of line 341 “postp.0.class = de.cm.osm2po.plugins.postp.PgRoutingWriter”. This will have “osm2po” output topology in a format that we can read with pgRouting.  Save the config and run `java -Xmx512m -jar osm2po-core-5.5.5-signed.jar cmd=c prefix=lisbon /mnt/c/osm2pgsql_guide/Lisbon.pbf`, replacing the paths once again with your own.  Now we just need to add this data to our data base, which we can do using `psql -host localhost -port 5432 -U postgres -d postgres -q -f lisbon_2po_4pgr.sql`, once again replacing paths.  If it isn't responding to psql commands in the terminal, you might have to add `C:\Program Files\PostgreSQL\16\bin` and  `C:\Program Files\PostgreSQL\16\lib` to the System Paths section.  
Once this is done, you're ready to run pgrouting! 

### Step 3:  Using PGRouting

Begin by checking extensions using `CREATE EXTENSION postgis;` and `CREATE EXTENSION pgrouting;`.  If these are both added, try running this (Replacing starting and ending latitudes and longitudes with ones that exist in chosen data region):
```
WITH start AS (
  SELECT topo.source --could also be topo.target
  FROM lisbon_2po_4pgr as topo
  ORDER BY topo.geom_way <-> ST_SetSRID(
    ST_GeomFromText('POINT (-9.144035 38.737524)'),
  4326)
  LIMIT 1
),
-- find the nearest vertex to the destination longitude/latitude
destination AS (
  SELECT topo.target --could also be topo.target
  FROM lisbon_2po_4pgr as topo
  ORDER BY topo.geom_way <-> ST_SetSRID(
    ST_GeomFromText('POINT (-9.1545999491376 38.73023147131511)'),
  4326)
  LIMIT 1
)
-- use Dijsktra and join with the geometries
SELECT ST_Union(geom_way) as route
FROM pgr_dijkstra('
    SELECT id,
         source,
         target,
         ST_Length(ST_Transform(geom_way, 3857)) AS cost
        FROM lisbon_2po_4pgr',
    array(SELECT source FROM start),
    array(SELECT target FROM destination),
    directed := false) AS di
JOIN   lisbon_2po_4pgr AS pt
  ON   di.edge = pt.id;
```
