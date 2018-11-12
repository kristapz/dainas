This scrapes the old faulkner site built with Apache Cocoon and Solr, and converts it to plain HTML/CSS and Solr(?) or maybe some other search product.

To scrape the old site:
- `wget --mirror --no-host-directories --no-parent --page-requisites --convert-links --convert-file-only --adjust-extension --directory-prefix=static-content http://latviandainas.lib.virginia.edu`

TODO:
