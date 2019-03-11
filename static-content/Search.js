const theURL = 'https://latviandainas.lib.virginia.edu/solr/latcore/select?rows=80000&'


function xhrSuccess() { 
    this.callback.apply(this, this.arguments); 
    removeLoader();
}

function xhrError() { 
    console.error(this.statusText); 
}

function loadResults(url, callback /*, opt_arg1, opt_arg2, ... */) {
    const xhr = new XMLHttpRequest();
    xhr.callback = callback;
    xhr.arguments = Array.prototype.slice.call(arguments, 2);
    xhr.onload = xhrSuccess;
    xhr.onerror = xhrError;
    xhr.open("GET", url, true);
    xhr.send(null);
}

function showMessage(message) {
    console.log(message + this.responseText);
}

function querySolr() {
    const urlParams = new URLSearchParams(window.location.search);
    const myParam = urlParams.get('action');
    //if ("Submit" == myParam ) {
    if (window.location.search.indexOf('action')) {
        const query = buildQueryURL();
        loadResults(query, displayResult);
    } else {
        removeLoader();
    }
}

function buildQueryURL() {

    const urlParams = new URLSearchParams(window.location.search)
    const fulltext = urlParams.get('searchText');

    //const query = theURL + 'hl=on&hl.fl=fulltext&fq=type:' + type + '&q=fulltext:"' + fulltext + '"'
    const query = theURL + 'q=fulltext:' + fulltext

    return query;
}

/** Displays the results from solr.
  * Manipulates the search.html page, adding a div to display the number of
  * results, and a list of each item from the search results.
  *
  * @param {object} searchRequest - The JSON object returned by the solr database; the search results.
*/
function displayResult() {
    const jObj = JSON.parse(this.response);
    const resultDiv = document.getElementById("searchResult");

    const numResults = document.createElement("div");
    resultDiv.appendChild(numResults);
    numResults.innerHTML = "Results Found: " + jObj.response.numFound;

    const resultList = document.createElement("ul");
    resultDiv.appendChild(resultList);
    var theClass = "result_div_odd";
    jObj.response.docs.forEach(function(item, index){
        if ( (index+1)%2 == 0 ){
            theClass = "result_div_even";
        } else {
            theClass = "result_div_odd";
        }

        //var highlight = jObj.highlighting[item.id].fulltext;
        // need to figure out lang variable
        var volume = setVolume(item.volume_id);
        var htmlStuff = 
            '<li class="'+ theClass +'">' +
                '<p>' +
                '<a href="tei.'+ item.volume_id +'.xml?lang=eng&amp;div_id='+ item.id +'">'+ item.lg_head +'</a>' +
                '<br> From <a href="tei.'+ item.volume_id +'.xml?lang=eng&amp;div_id='+ item.parent_id +'">'+ item.parent_head +'</a>, '+ volume +'</p>' +
            '</li>';


        resultList.innerHTML += htmlStuff;
    });
}

function removeLoader() {
    var loader = document.getElementById('loader');
    loader.remove();
}


function setVolume(volume_id) {
    var volume = {
        'latv01': 'I',
        'latv02': 'II',
        'latv03': 'III',
        'latv04': 'IV',
        'latv05': 'V',
        'latv06': 'VI',
        'latv07': 'VII',
        'latv08': 'VIII',
        'latv09': 'IX',
        'latv10': 'X',
        'latv11': 'XI',
        'latv12': 'XII'
    };

    return "Volume " + (volume[volume_id]);
}



// One time use function to create a temporary page (grover/grover.html) that
// lists all of the records from the solr database. The list is then saved to
// the production site so that each of the individual bibliography pages are
// linked to, which will then allow the scrape to generate a static file for
// each bib. page.
/*
function allFromSolr() {
  var query = theURL + "q=*:*";
  if (request) {
    request.open('GET', query, true);
    request.onreadystatechange = function() {
      if (request.readyState == 4 && request.status == 200) {
          var jObj = JSON.parse(request.response);
          var resultDiv = document.getElementById("allResults");

          var numResults = document.createElement("div");
          resultDiv.appendChild(numResults);
          numResults.innerHTML = "Results Found: " + jObj.response.numFound;

          var resultList = document.createElement("ul");
          resultDiv.appendChild(resultList);
          var theClass = "result_odd";
          jObj.response.docs.forEach(function(item, index){
            if ( (index+1)%2 == 0 ){
              theClass = "result_even";
            } else {
              theClass = "result_odd";
            }

            var text = item.id + ". " + item.title;
            resultList.innerHTML += "<li class='" + theClass + "'>" + "<a href='http://faulkner.lib.virginia.edu/media%3fid=" + item.id.trim() + "'>" + text + "</a></li>";
          });

      }
    }
    request.send();
  } else {
    document.getElementById("searchError").textContent = "There was a problem connecting to solr.";
  }
}
*/
