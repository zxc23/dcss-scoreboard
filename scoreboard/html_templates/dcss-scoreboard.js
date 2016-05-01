// Load the list of players and set up player autocomplete
var ajax = new XMLHttpRequest();
ajax.open("GET", "{{ urlbase }}/static/js/players.json", true);
ajax.onload = function() {
  var list = JSON.parse(ajax.responseText);
  new Awesomplete(
      document.querySelector("#playersearch"),
      { list: list, filter: Awesomplete.FILTER_STARTSWITH }
  );
};
ajax.send();
// Handle selecting a usernames
$('document').ready(function() {
  document.querySelector("#playersearch").addEventListener("awesomplete-selectcomplete", function() {
    window.location.href = '{{ urlbase }}/players/' + document.querySelector("#playersearch").value + '.html';
  });
});

// Convert all timestamps to relative
jQuery(document).ready(function() {
  jQuery("time.timeago").timeago();
});
