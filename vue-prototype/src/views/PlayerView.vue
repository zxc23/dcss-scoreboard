<style scoped>
  .stats {
    margin: 1rem 0;
    border-top: 1px solid rgba(0, 0, 0, 0.1);
    border-bottom: 1px solid rgba(0, 0, 0, 0.1);
    padding: 1rem 0 0.5rem 0;
    display: flex;
    flex-wrap: wrap;
  }

  .stats-column {
    flex: 1;
  }

  .stat-label {
    font-weight: bold;
  }
</style>

<template>
  <div class="container">
    <app-header></app-header>
    <div>
      <h2>{{ player }}</h2>
    </div>
    <div class="stats">
      <div class="stats-column">
        <p><span class="stat-label">Last Active:</span> {{ last_active }}</p>
        <p><span class="stat-label">Games Played:</span> {{ games_played }}</p>
        <p><span class="stat-label">Wins:</span> {{ num_wins }}</p>
        <p><span class="stat-label"><abbr title="Including leaving and wizmode">Quits</abbr>:</span> {{ num_quits }}</p>
      </div>
      <div class="stats-column">
        <p><span class="stat-label">Total Playtime:</span> {{ total_playtime }}</p>
        <p><span class="stat-label">Highest Score:</span> {{ highest_score }}</p>
        <p><span class="stat-label">Shortest Win:</span> {{ shortest_win }}</p>
        <p><span class="stat-label">Fastest Win:</span> {{ fastest_win }}</p>
      </div>
      <div class="stats-column">
      </div>
      <div class="stats-column">
      </div>
    </div>
  </div>
</template>

<script>
  import AppHeader from '../components/AppHeader'
  
  // Access API for data here

  export default {
    components: {
      AppHeader
    },
    props: ['player'],
    data: function () {
      return {
        last_active: 'Some day',
        games_played: '150',
        num_wins: '123 (96.4%)',
        num_quits: '15 (3.1%)',
        total_playtime: '646 hours',
        highest_score: '45,546,240 points',
        shortest_win: '9,743 turns',
        fastest_win: '00:41:00 hours'
      }
    },
    name: 'player-view'
  }
</script>
