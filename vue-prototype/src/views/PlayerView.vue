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
    <div v-if="api_loaded">
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
          <p><span class="stat-label">Total Playtime:</span> {{ total_playtime }} hours</p>
          <p><span class="stat-label">Highest Score:</span> {{ highest_score.score }} points</p>
          <p v-if="num_wins > 0"><span class="stat-label">Shortest Win:</span> {{ shortest_win.turns }} turns</p>
          <p v-if="num_wins > 0"><span class="stat-label">Fastest Win:</span> {{ fastest_win.dur }} hours</p>
        </div>
        <div class="stats-column">
        </div>
        <div class="stats-column">
        </div>
      </div>
    </div>
  </div>
</template>

<script>
  import AppHeader from '../components/AppHeader'
  import _ from 'lodash'

  export default {
    components: {
      AppHeader
    },
    props: ['player'],
    data: function () {
      return {
        api_loaded: false,
        wins: [],
        last_active: 'Some day',
        num_quits: 15,
        total_playtime: 646
      }
    },
    computed: {
      games_played: function () {
        return this.wins.length
      },
      num_wins: function () {
        return this.wins.length
      },
      highest_score: function () {
        return _.maxBy(this.wins, function (g) {
          return g.score
        })
      },
      shortest_win: function () {
        return _.minBy(this.wins, function (g) {
          return g.turns
        })
      },
      fastest_win: function () {
        return _.minBy(this.wins, function (g) {
          return g.dur
        })
      }
    },
    name: 'player-view',
    created: function () {
      // Access API
      this.axios.get('static/api/1/player/wins/' + this.player)
      .then((response) => {
        this.wins = response.data
        this.api_loaded = true
      })
      .catch((err) => {
        console.log(err)
      })
    }
  }
</script>
