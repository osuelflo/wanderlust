## Installation Process for MacOS
### Step 1: Installing Homebrew

Majority of this installation guide was taken from [this tutorial](https://www.codementor.io/@engineerapart/getting-started-with-postgresql-on-mac-osx-are8jcopb).
Homebrew is a package manager that is popular on MacOS. To install it, copy and paste the following command into your command line:
`/usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"`.
### Step 2: Installing Postgres, postgis, and pgrouting

Run the following command to install PostgreSQL:
`brew install postgresql`.
Run the following command to install postgis:
`brew install postgis`.
Run the following command to install pgrouting:
`brew install pgrouting`.
Homebrew will take care of installing any required dependencies. To start up Postgres, run the command:
`brew services start postgresql`.

### Step 3: Configuring Postgres

Postgres automatically creates the user `postgres`. Let's hop into the psql command line. To do this, enter the command:
`psql postgres`.
Try entering `\du` into the psql command line to show all users. Postgres has conveniently created a user that matches your username! However, let's create our own superuser. You can enter
`CREATE ROLE username WITH LOGIN PASSWORD 'quoted password'` into the `postgres=#` command line. Change username to whatever you'd like, as with `quoted password`. Now, let's try using the `ALTER ROLE` command to give this new user superuser powers (this is important for creating extensions for our database, which you will have to do). Enter `ALTER ROLE username SUPERUSER` to give this new user superuser powers. 

Another important point: to quit Postgres, simply enter `\q`.

### Step 4: Create a database and extensions

To create a database, let's first hop back into Postgres, this time as the new user we created:
`psql postgres -U new_user`.
Now, to create a database, we can do:
`CREATE DATABASE db_name`.
To connect to that database, simply enter:
`\connect db_name`.
Now, let's create our two extensions. Enter:
`CREATE EXTENSION postgis;`.
Then, enter
`CREATE EXTENSION pgrouting;`.
Yay! We've got a new database that has our two extensions up and running.

### Step 5 (Optional): Connect to a GUI client such as PgAdmin4

Here are the instructions from the tutorial:
1. Download it at https://www.pgadmin.org/download/macos4.php
2. Double-click the downloaded disc image (DMG) file in your Downloads folder
3. Drag the pgAdmin 4 app to your Applications folder
4. Find pgAdmin in Launchpad and launch the app.

Next, we must create a server:
1. Right-click on ‘Servers’ and select Register => Server
2. Give it an easy to remember name and uncheck the “Connect Now” box
3. For server address, enter localhost
4. You can leave the default values entered in the boxes
5. Change the user to the user you created.

Click save, and then you will be prompted to enter the password you created above.

### Step 6:  Converting OSM Data to Data for PGRouting
https://pimylifeup.com/macos-path-environment-variable/ - For path environment
https://osxdaily.com/2018/07/05/where-homebrew-packages-installed-location-mac/ - for finding where your homebrew package is installed.

PGRouting needs a certain data structure in order to operate, and raw OSM files have to be passed through two conversion programs.  The first step is to convert an OSM data file to one that PSQL can handle using osm2pgsql, which can be ofund [here](https://osm2pgsql.org/doc/install.html). Then, the path to the directory containing the osm2pgsql executable file must be added to the path environment variables. To do this, we first need to locate where the executable is. We can do
`brew --prefix [package]` 
to find the location.
To add it to the path environment variable, we can follow these steps:

"The way that macOS recommends is to add a file into the “/etc/paths.d/” directory. When you start a new terminal session, macOS will automatically read these files and add the folders to your path environment variable."
1. Create a new file in the directory by entering: `sudo nano /etc/paths.d/my_file_name`. Name it something descriptive.
2. Now, add the path to the osm2pgsql executable we found above to the file.
Done! You can exit the editor.

Next, we will want to download some OSM data. We are going to choose to get all of OSM data for Minnesota. We did this using [geofabrik](https://www.geofabrik.de/) in the pbf format.  The default style must also be downloaded, here is a [link](https://learnosm.org/files/default.style).

Now that that is done, we can load this data to our database:

`osm2pgsql -c -d DATABASE_NAME -U USER_NAME -H localhost -r pbf -W -S PATH_TO_DEFAULT.STYLE PATH_TO_MN_DATA`

Be sure to replace the stuff in all caps with the relevant information.

We have one more conversion to do to get it to become data that can be used by pgRouting.  Download [osm2po](https://osm2po.de/), unzip the folder, then open the config file. Change line 190 (might be a different line) to “wtr.finalMask = car,foot,bike”. This will filter the OSM data to segments with these tags, uncomment lines 221 to 230 (might be different lines - just find the lines near 221 that are commented) (This makes sure that we have access to all types of paths in our routing calculation), then Uncomment (remove the “#” at the beginning) of line 341 “postp.0.class = de.cm.osm2po.plugins.postp.PgRoutingWriter”. This will have “osm2po” output topology in a format that we can read with pgRouting.  Save the config and run `java -Xmx512m -jar osm2po-core-5.5.5-signed.jar cmd=c prefix=minnesota PATH_NAME_TO_OSM.PBF_FILE`, replacing the paths once again with your own.  Now we just need to add this data to our data base, which we can do using `psql -h localhost -p 5432 -U USER_NAME -d DB_NAME -q -f "PATH"`, once again replacing paths. The `PATH` should be the one that is generated under the `commandline template` line in the terminal. That output is produced after you have run the first command in this paragraph.
Once this is done, you're ready to run pgrouting! LETS GO


