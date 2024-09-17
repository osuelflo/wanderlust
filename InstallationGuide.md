# Installation Process
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

### Step 3:  Testing PGRouting

Begin by checking extensions in a tool like pgAdmin using `CREATE EXTENSION postgis;` and `CREATE EXTENSION pgrouting;`.  If these are both added, try running this query to see if you're given a route. You should be able to visualize this in the same tab where you run the query. Remember to replace the starting and ending latitudes and longitudes with ones that exist in chosen data region.
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

### Step 4. Using Postgres through Javascript
- First, run the PythonHTTPServer file
  - If this is the first time using this file, you may have to install the psycopg2 library. Just run 'pip install psycopg2' in the correct directory and you should be good
  - This will begin running a server in the background of your computer running out of your localhost
  - Make sure that you update the database name, password, and port number to match your specific postgres setup
    - You may also have to update the prefix on your geospatial data files in the SQL query
  - If you make any changes to this Python file, or want to close the server at any point, you can just close the Python terminal in VSCode
    - If you change the Python file but don't close the terminal, your changes won't be used by the server

- Now that this server is running, you should be ready to use Wanderlust's basic functionality!

- To do so, open wanderlust.html
  - There will be two slots to enter addresses. Go ahead and enter two addresses in Minnesota
  	- Our address matching system has some particular naming conventions, so it will autocorrect extra words (like Macalester -> Macalester College), but won't do so for partial words (like Mac -> Macalester)
  - For now, don't adjust the Distance dropdown menu, because we haven't set up our alternative routing approaches yet!
  - Instead, just click Get Route, and give Postgres some time to find your route
  - Once it has, you should see the route on your screen!
  - Yippeee!!!
 
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

An issue with this query is that some things are marked as footpaths in sql that are not actually particularly pleasant, as they are sidewalks to major streets.  The version below finds the nearest path to every other considered pedestrian path, and checks if it's a major road, in which case it doesn't decrease the weight. To solve this, we'll create yet another new collumn, this time marking whether a large street exists within a certain threshold a given line segment.  The query should look something like this:

```
CREATE INDEX way_gix ON planet_osm_line USING GIST(way);
CREATE INDEX highway_gix ON planet_osm_line (highway); --Creating indexes to make operations faster
VACUUM ANALYZE planet_osm_line;
ALTER TABLE twincities_2po_4pgr ADD COLUMN "highway_true" boolean; --Result column

WITH highways AS (SELECT way FROM planet_osm_polygon
				  WHERE highway IN ('motorway', 'trunk', 'primary', 'secondary'))
UPDATE twincities_2po_4pgr as t  --marks the table we're updating as t
SET highway_true = --Marks the column  we're setting
 		(SELECT COUNT(*) FROM 
 		 (SELECT 1 FROM highways WHERE highways.way::geometry <-> l.way::geometry < 20 LIMIT 1) 
		 ) > 0  --Checks if a road exists that is major within a distance radius
FROM planet_osm_polygon AS l --Specifies the table we're getting line data from
WHERE t.osm_id = l.osm_id; --Makes sure that our cost column corresponds to the correct osm_ids in both tables

```
This will take a while to run, depending on the size of your dataset.  For the twin cities, it took just over 4 hours.  It's worth it though, because now we have a way of knowing if a path is a sidewalk on a major street or pleasant residential walking trail.  It's time to weigh our edges once more, this time using our new column:

```
UPDATE twincities_2po_4pgr as t  --marks the table we're updating as t
SET ped_bike_pref = --Marks the column  we're setting
--l.highway IN ('footway', 'pedestrian', 'cycleway', 'track', 'steps')
CASE WHEN --If statement
	(t.highway_true = true) --The tags that we want (stored in the "highway" column of a line/polygon)
THEN
	CASE WHEN 
		(l.highway IN ('footway', 'pedestrian', 'cycleway', 'track', 'steps'))
	THEN
		ST_Length(ST_Transform(geom_way, 3857))/5 --Length/1000
	WHEN
		(l.highway IN ('living_street', 'tertiary'))
	THEN
		ST_Length(ST_Transform(geom_way, 3857))/3
	ELSE
		ST_Length(ST_Transform(geom_way, 3857))
	END
ELSE
	CASE WHEN 
		(l.highway IN ('footway', 'pedestrian', 'cycleway', 'track', 'steps'))
	THEN
		ST_Length(ST_Transform(geom_way, 3857))/100 --Length/1000
	WHEN
		(l.highway IN ('living_street', 'tertiary'))
	THEN
		ST_Length(ST_Transform(geom_way, 3857))/10
	ELSE
		ST_Length(ST_Transform(geom_way, 3857))/2
	END
END
	 
FROM planet_osm_line AS l --Specifies the table we're getting line data from
WHERE t.osm_id = l.osm_id; --Makes sure that our cost collumn corresponds to the correct osm_ids in both tables

-- Same code here but run on the planet_osm_polygon table
UPDATE twincities_2po_4pgr as t
SET ped_bike_pref =
CASE WHEN --If statement
	(t.highway_true = true) --The tags that we want (stored in the "highway" column of a line/polygon)
THEN
	CASE WHEN 
		(l.highway IN ('footway', 'pedestrian', 'cycleway', 'track', 'steps'))
	THEN
		ST_Length(ST_Transform(geom_way, 3857))/5 --Length/1000
	WHEN
		(l.highway IN ('living_street', 'tertiary'))
	THEN
		ST_Length(ST_Transform(geom_way, 3857))/3
	ELSE
		ST_Length(ST_Transform(geom_way, 3857))
	END
ELSE
	CASE WHEN 
		(l.highway IN ('footway', 'pedestrian', 'cycleway', 'track', 'steps'))
	THEN
		ST_Length(ST_Transform(geom_way, 3857))/100 --Length/1000
	WHEN
		(l.highway IN ('living_street', 'tertiary'))
	THEN
		ST_Length(ST_Transform(geom_way, 3857))/10
	ELSE
		ST_Length(ST_Transform(geom_way, 3857))/2
	END
END
FROM planet_osm_polygon AS l
WHERE t.osm_id = l.osm_id;
```

This should be a pretty reasonable routing engine for walking paths, if one that doesn't mind taking a meandering route.  Now let's try creating a weight system for biking:

```
ALTER TABLE twincities_2po_4pgr ADD COLUMN "bike_pref" float;
UPDATE twincities_2po_4pgr as t  --marks the table we're updating as t
SET bike_pref = --Marks the column  we're setting
--l.highway IN ('footway', 'pedestrian', 'cycleway', 'track', 'steps')
CASE WHEN --If statement
	(t.highway_true = true) --The tags that we want (stored in the "highway" column of a line/polygon)
THEN
	CASE WHEN 
		(l.highway IN ('footway', 'pedestrian', 'track', 'steps'))
	THEN
		9000
	WHEN
		(l.highway IN ('living_street', 'tertiary'))
	THEN
		ST_Length(ST_Transform(geom_way, 3857))/3
	WHEN
		(l.highway IN ('cycleway') OR l.bicycle IN ('yes', 'designated'))
	THEN
		ST_Length(ST_Transform(geom_way, 3857))/5
	ELSE
		ST_Length(ST_Transform(geom_way, 3857))
	END
ELSE
	CASE WHEN 
		(l.highway IN ('footway', 'pedestrian', 'track', 'steps'))
	THEN
		9000
	WHEN
		(l.highway IN ('living_street', 'tertiary'))
	THEN
		ST_Length(ST_Transform(geom_way, 3857))/10
	WHEN
		(l.highway IN ('cycleway') OR l.bicycle IN ('yes', 'designated'))
	THEN
		ST_Length(ST_Transform(geom_way, 3857))/100
	ELSE
		ST_Length(ST_Transform(geom_way, 3857))
	END
END
	 
FROM planet_osm_line AS l --Specifies the table we're getting line data from
WHERE t.osm_id = l.osm_id; --Makes sure that our cost collumn corresponds to the correct osm_ids in both tables

-- Same code here but run on the planet_osm_polygon table
UPDATE twincities_2po_4pgr as t
SET bike_pref =
CASE WHEN --If statement
	(t.highway_true = true) --The tags that we want (stored in the "highway" column of a line/polygon)
THEN
	CASE WHEN 
		(l.highway IN ('footway', 'pedestrian', 'track', 'steps'))
	THEN
		9000
	WHEN
		(l.highway IN ('living_street', 'tertiary'))
	THEN
		ST_Length(ST_Transform(geom_way, 3857))/3
	WHEN
		(l.highway IN ('cycleway') OR l.bicycle IN ('yes', 'designated'))
	THEN
		ST_Length(ST_Transform(geom_way, 3857))/5
	ELSE
		ST_Length(ST_Transform(geom_way, 3857))
	END
ELSE
	CASE WHEN 
		(l.highway IN ('footway', 'pedestrian', 'track', 'steps'))
	THEN
		9000
	WHEN
		(l.highway IN ('living_street', 'tertiary'))
	THEN
		ST_Length(ST_Transform(geom_way, 3857))/10
	WHEN
		(l.highway IN ('cycleway') OR l.bicycle IN ('yes', 'designated'))
	THEN
		ST_Length(ST_Transform(geom_way, 3857))/100
	ELSE
		ST_Length(ST_Transform(geom_way, 3857))
	END
END
FROM planet_osm_polygon AS l
WHERE t.osm_id = l.osm_id;
```
Yay!  Now we have a few different weighting systems for generating routes.  Now you can feel free to use the dropdown menu to pick your own route-selection style.