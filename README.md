# wanderlust
## Installation Process
### Step 1:  Installing PostgreSQL and PostGIS

Install PostgreSQL from [This Link](https://www.enterprisedb.com/downloads/postgres-postgresql-downloads).
Follow the prompts, pay attention to the server details (Listening port, etc.), then once finished check the box to launch stack builder.  
Follow prompts once more until the option to add spatial extensions appears, under which we checked the box for PostGIS. Once this is complete, pgAdmin can be opened and used to create a database, and `CREATE EXTENSION postgis;` can be used to add the extension.

- config file changes
- specific version
  
This was all done according to [this tutorial](https://mapscaping.com/getting-started-with-postgis/).

### Step 2:  Converting OSM Data to Data for PGRouting

PGRouting needs a certain data structure in order to operate, and raw OSM files have to be passed through two conversion programs.  The first step is to convert an OSM data file to one that PSQL can handle using osm2pgsql, which can be found [here](https://osm2pgsql.org/doc/install.html).  Then, the path to the directory containing the osm2pgsql executable file must be added to the path environment variables (within the System Envirment variables section), added in the "Edit System Environment Variables" menu.  The next step is to get an OSM file, we did this using [geofabrik](https://www.geofabrik.de/) in the pbf format.  The default style must also be downloaded, here is a [link](https://learnosm.org/files/default.style).  Once all these steps are complete, this command `osm2pgsql -c -d postgres -U postgres -H localhost -r pbf -W -S C:\osm2pgsql_guide\default.style C:\osm2pgsql_guide\Lisbon.osm.pbf`  The paths should be replaced with your own, and the database should be whatever you named it.  The data should now exist in PGAdmin in your database.  

We have one more conversion to do to get it to become data that can be used by pgRouting.  Download [osm2po](https://osm2po.de/), unzip the folder, then open the config file. Change line 190 to “wtr.finalMask = car,foot,bike”. This will filter the OSM data to segments with these tags, uncomment lines 221 to 230 (This makes sure that we have access to all types of paths in our routing calculation), then Uncomment (remove the “#” at the beginning) of line 341 “postp.0.class = de.cm.osm2po.plugins.postp.PgRoutingWriter”. This will have “osm2po” output topology in a format that we can read with pgRouting.  Save the config and run `java -Xmx512m -jar osm2po-core-5.5.5-signed.jar cmd=c prefix=lisbon /mnt/c/osm2pgsql_guide/Lisbon.pbf`, replacing the paths once again with your own.  Now we just need to add this data to our data base, which we can do using `psql -h localhost -p 5432 -U postgres -d postgres -q -f "C:\Users\minnesota\minnesota_2po_4pgr.sql"`, once again replacing paths.  If it isn't responding to psql commands in the terminal, you might have to add `C:\Program Files\PostgreSQL\16\bin` and  `C:\Program Files\PostgreSQL\16\lib` to the System Paths section.  
Once this is done, you're ready to run pgrouting! 

### Step 3:  Using PGRouting

Begin by checking extensions using `CREATE EXTENSION postgis;` and `CREATE EXTENSION pgrouting;`.  If these are both added, try running this (Replacing starting and ending latitudes and longitudes with ones that exist in chosen data region):
```
WITH start AS (
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
SELECT ST_Union(geom_way) as route
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
  ON   di.edge = pt.id;
```
This returns coordinates sorta
```
WITH start AS (
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
  ON   di.edge = pt.id;
```

### Step 4. Using Postgres through Javascript
- First, run the PythonHTTPServer file
  - If this is the first time using this file, you may have to install the psycopg2 library. Just run pip install psycopg2 in the correct directory and you should be good
  - This will begin running a server in the background of your computer running out of your localhost
  - Make sure that you update the database name, password, and port number to match your specific postgres setup
    - You may also have to update the prefix on your minnesota files in the SQL query - I changed my name to minnesota, so hopefully not
  - If you make any changes to this Python file, or want to close the server at any point, you can just close the Python terminal in VSCode
    - If you change the Python file but don't close the terminal, your changes won't be used by the server


- Then, open the postgresJavascriptTest.html file
  - There should be a text input slot for your start and end coordinates
    - put coordinates into those slots, removing the comma that clicking the map will include
  - Pressing the Get Postgres Route button will pass those two slots into pgrouting and respond with the result of the HTTP request to our python server into the polyline input text box
    - ### BUG HERE!
      - Right now, basically any route that isn't the one we calibrated on (the St. Paul to Duluth route) will give us some weird ass route that just runs along the Wisconsin border
      - I'm not sure why. I think James knows more about the Query process than I do. Looks like it generates a route that doesn't actually connect the two corods we give it
        - I think it has to do with the SRID 4326 in the start/destination section. Maybe it's selecting a weird topography target
      - If you want to just make the route appear, you can steal the original coords for the calibration route from the pythonPostgresTest.py file - when the coords are the same as our originals it works
        - Those coords are -93.167165 44.936098 for the start and -90.337104 47.751911 for the destination

- Then you should just be able to add the polyline from our polyline button

### Step 5:  Adding Custom Edge Weights

First, we need to add a column to our table.  For our first edited version, we're going to create a column of edge costs that prioritizes pedestrian and biking tracks.  We'll call this new column `ped_bike_pref`.  The sql query looks like this: `ALTER TABLE minnesota_2po_4pgr ADD COLUMN "ped_bike_pref" float;`. Now we have to run a query to update this new column with some weights.  In this case we will edit the weights simply in that we will just divide the cost of any line or polygon that has a category that matches what we want by 1000.  The query is as follows (Took me just over minute to run):
```
-- We have our edges stored in two locations, the line table and polygon table.  We must run our logic on both.
UPDATE minnesota_2po_4pgr as t  --marks the table we're updating as t
SET ped_bike_pref = --Marks the column  we're setting
CASE WHEN --If statement
	(l.highway IN ('footway', 'pedestrian', 'cycleway', 'track', 'steps')) --The tags that we want (stored in the "highway" column of a line/polygon)
THEN
	ST_Length(ST_Transform(geom_way, 3857))/1000 --Length/1000
ELSE
	ST_Length(ST_Transform(geom_way, 3857)) --Just length
END
FROM planet_osm_line AS l --Specifies the table we're getting line data from
WHERE t.osm_id = l.osm_id; --Makes sure that our cost collumn corresponds to the correct osm_ids in both tables

-- Same code here but run on the planet_osm_polygon table
UPDATE minnesota_2po_4pgr as t
SET ped_bike_pref =
CASE WHEN
	(l.highway IN ('footway', 'pedestrian', 'cycleway', 'track', 'steps'))
THEN
	ST_Length(ST_Transform(geom_way, 3857))/1000
ELSE
	ST_Length(ST_Transform(geom_way, 3857))
END
FROM planet_osm_polygon AS l
WHERE t.osm_id = l.osm_id;
```

Now we should be set to run our route finder query again, but we can replace `ST_Length(ST_Transform(geom_way, 3857))` with `ped_bike_pref`.

An issue with this query is that some things are marked as footpaths in sql that are not actually particularly pleasant, as they are sidewalks to major streets.  The version below finds the nearest path to every other considered pedestrian path, and checks if it's a major road, in which case it doesn't decrease the weight.
(This took me 28 minutes to run so strap in)

```
-- We have our edges stored in two locations, the line table and polygon table.  We must run our logic on both.
UPDATE minnesota_2po_4pgr as t  --marks the table we're updating as t
SET ped_bike_pref = --Marks the column  we're setting
CASE WHEN --If statement
	(l.highway IN ('footway', 'pedestrian', 'cycleway', 'track', 'steps', 'path')) --The tags that we want (stored in the "highway" column of a line/polygon)
THEN
	CASE WHEN
		((SELECT COUNT(*) FROM --Gets number of nearby lines that are major
		  (SELECT highway, line.way <-> ST_AsEWKT(l.way)::geometry AS dist --Creates a distance column
		   FROM planet_osm_line AS line --checks against all other lines
		   ORDER BY DIST) WHERE dist < 50 AND highway IN ('motorway', 'trunk', 'primary', 'secondary')) > 0) --Checks if nearest road is major
	THEN
		ST_Length(ST_Transform(geom_way, 3857))/10--Length/10
	ELSE
		ST_Length(ST_Transform(geom_way, 3857))/1000--Length/1000
	END
ELSE
	ST_Length(ST_Transform(geom_way, 3857)) --Just length
END
FROM planet_osm_line AS l --Specifies the table we're getting line data from
WHERE t.osm_id = l.osm_id; --Makes sure that our cost collumn corresponds to the correct osm_ids in both tables

-- Same code here but run on the planet_osm_polygon table
UPDATE minnesota_2po_4pgr as t
SET ped_bike_pref =
CASE WHEN
	(l.highway IN ('footway', 'pedestrian', 'cycleway', 'track', 'steps', 'path'))
THEN
	CASE WHEN
		((SELECT COUNT(*) FROM --Same as Above
		  (SELECT highway, line.way <-> ST_AsEWKT(l.way)::geometry AS dist --Creates a distance column
		   FROM planet_osm_polygon AS line --checks against all other lines
		   ORDER BY DIST) WHERE dist < 50 AND highway IN ('motorway', 'trunk', 'primary', 'secondary')) > 0) --Checks if nearest road is major
	THEN
		ST_Length(ST_Transform(geom_way, 3857))/10
	ELSE
		ST_Length(ST_Transform(geom_way, 3857))/1000--Length/1000
	END
ELSE
	ST_Length(ST_Transform(geom_way, 3857))
END
FROM planet_osm_polygon AS l
WHERE t.osm_id = l.osm_id;
```
