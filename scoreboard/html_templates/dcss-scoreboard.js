// Load the list of players and set up player autocomplete
const ajax = new XMLHttpRequest();
ajax.open("GET", "{{ urlbase }}/static/js/players.json", true);
ajax.onload = function() {
  var list = JSON.parse(ajax.responseText);
  new Awesomplete(
      document.querySelector("#playersearch"),
      { list: list, filter: Awesomplete.FILTER_STARTSWITH }
  );
};
ajax.send();

$('document').ready(function () {
  // Handle selecting a usernames
  document.querySelector("#playersearch").addEventListener("awesomplete-selectcomplete", function() {
    window.location.href = '{{ urlbase }}/players/' + document.querySelector("#playersearch").value + '.html';
  });

  // Convert all timestamps to relative
  jQuery.timeago.settings.strings = {
    prefixAgo: null,
    prefixFromNow: null,
    suffixAgo: "ago",
    suffixFromNow: "from now",
    seconds: "a minute",
    minute: "a minute",
    minutes: "%d minutes",
    hour: "an hour",
    hours: "%d hours",
    day: "a day",
    days: "%d days",
    month: "a month",
    months: "%d months",
    year: "a year",
    years: "%d years",
    wordSeparator: " ",
    numbers: []
  };
  jQuery("time.timeago").timeago();
  
  // Enable tooltips
  $('abbr').tooltip();

  // Enable games accordion toggle
  var show_games = false;
  $('#oldwinstoggle').click(function () {
    show_games = !show_games;
    $('.old-game').css({ 'display': show_games ? 'table-row' : 'none' });
    const old_text = $('#oldwinstoggle').text();
    $('#oldwinstoggle').text(((show_games) ? 'Hide' : 'Show') + old_text.substr(4));
    return false;
  });
});
