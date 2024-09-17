# Wanderlust

Wanderlust is a web application that generates routes between locations in Minnesota.

## Usage
1. Set up your PostgresSQL and PGRouting database using the [Installation Guide](InstallationGuide.md). (This is a pretty complicated/time-consuming process right now! Check out our Next Steps to see how we would fix this if we were to commit more time to this project)
2. Open wanderlust.html in your web browser of choice
3. Run pythonHTTPServer.py, and leave it running in the background
4. Now you're ready to use Wanderlust! 
    - Type the two addresses you'd like to route between into the address slots, and click on the button associated with each address
    - Select the routing type you'd like to use from the drop-down menu
    - Get your route!



## Known Bugs
- Sometimes the visuals for the generated route don't properly scale with the view scale

## Next Steps
We made this project over the course of a single semester, when we had no prior experience with HTML, CSS, JavaScript, or an SQL language of any variety. We also had three other classes we were juggling classwork for! Because of that, we have many features we'd like to add/improve that we simply didn't have time for. Most notably:

- Improve the installation process!
    - The installation process is long, arduous, and poorly documented. We'd like to refactor the project so that each individual user doesn't need to do the entire database creation process. Some ways we've thought of to do that:
        1. Host the SQL server online somewhere, like an AWS EC2 or RDS. This is the ideal option, but the affordable versions of both of these might not provide the processing power to generate routes as quickly as we'd like
        2. Have a pre-generated SQL database available for download somewhere. This would still add extra steps for the user in the installation process, but they wouldn't have to wait through the actual creation process
- Better error reporting!
    - When errors happen while generating routes, they come from two particular places: either our pgrouting system (the SQL query) didn't work, or the local variables we have to represent the route didn't update properly. Right now, our error messages don't distinguish between these options at all, and it's difficult for users to know what they need to change/fix to address the error.