This repo contains the files scraped from the old latvian site built with
Apache Cocoon and Solr, and converted to plain HTML/CSS and Solr.

********************************
# Process for creating a clone

These were the steps used to recreate the old production site from Apache Cocoon and Solr.

It consists of using docker-compose with two images that work together to
provide static files and the Solr search.  The basic steps required to create
the images are outlined below, with detailed steps following.

- STATIC container: 
  - scrape the original website
  - copy any unlinked files
  - use the official nginx image with a local volume to copy in the modified default.conf file
  - modify the default.conf nginx file
  - change the search page to work with solr via javascript
  - create a javascript file to connect the search page and solr search engine
- SOLR container:
  - use the official solr image
  - change the managed-schema file
  - change the web.xml file
  - create a load-data script
  - have all the xml data files in place

## Create the STATIC container
- Scrape the old site:
    - `wget --mirror --no-host-directories --no-parent --page-requisites --convert-links --convert-file-only --adjust-extension --directory-prefix=static-content http://latviandainas.lib.virginia.edu`
- Edit the default nginx.conf file to serve files (and take care of file names
  with '?' in them.)

## Create the SOLR container
This uses a Dockerized solr to get an up to date solr and keep the search
functionality.

This uses a default solr docker image, and just plugs in some config files and
imports data into the core after the docker image is up and running.

The updated config files are:
- managed-schema
- web.xml

This set up uses a modified default solr script to create a core and import the
data into the index. `load-data` script is a modified copy of the solr script
`solr-demo` from
https://github.com/docker-solr/docker-solr/blob/master/scripts/solr-demo

The data is in the folder `add_docs` and are the xml file from the old server
that were used to build the index originally.

The solr container is built using docker-compose. There is a container for
nginx to serve the static files from the `static_content` directory. The solr
container is built from a default solr image and loads the config files and the
data via local volumes. The magic happens by calling the entrypoint section,
which determines the command and its parameters to be executed when the container
is run. In our case it calls solr's default docker-entrypoint.sh script which
just looks for a parameter of a named script to run from the
`/opt/docker-solr/scripts/` directory. This is where we place our modified
`solr-demo` script. This script is also looking for a parameter, the name of
the core it should create. This script runs solr, creates a default core, stops
solr, copies the config files from the local volumes into place over the
default files, restarts solr and loads the data into the index, stops solr,
then restarts solr in the foreground.

So the process goes:
execute `docker-entrypoint.sh` -> which runs `load-data` script which does all
the magic of creating a core and loading the data.

This happens each time the container is run.


# Development
- A docker-compose-dev.yml file is available for use locally or on production
  when traefik is used.
