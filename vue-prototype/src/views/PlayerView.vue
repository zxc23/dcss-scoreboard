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

  .win-columns {
    display: flex;
    flex-wrap: wrap;
  }

  .win-column {
    flex: 1;
    padding-right: 15px;
    padding-left: 15px;
  }

  .win-column:first-child {
    padding-left: 0;
  }

  .win-column:last-child {
    padding-right: 0;
  }

  .win-column-header {
    font-weight: bolder;
  }

  .fakelink {
    color: #0275d8;
    cursor: pointer;
  }

  .muted {
    color: #818a91;
  }

  .fakelink:hover, .active {
    color: #e29300;
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
          <p v-if="num_wins > 0"><span class="stat-label">Fastest Win:</span> {{ fastest_win.dur | prettydur }} hours</p>
        </div>
        <div class="stats-column">
        </div>
        <div class="stats-column">
        </div>
      </div>
      <div>
        <h3>Wins</h3>
        <div class="win-columns">
          <div class="win-column">
            <p class="win-column-header">By Species {{ num_species_won }}/{{ Object.keys(playable_species).length }}</p>
            <p>
              <span v-for="sp in playable_species" class="fakelink" :class="{ 'muted': !species_won[sp], 'active': species_filter.includes(sp) }" @click="filterSpecies(sp)">{{ sp }} ({{ species_won[sp] || 0 }}) </span>
            </p>
          </div>
          <div class="win-column">
            <p class="win-column-header">By Background {{ num_backgrounds_won }}/{{ Object.keys(playable_backgrounds).length }}</p>
            <p>
              <span v-for="bg in playable_backgrounds" class="fakelink" :class="{ 'muted': !backgrounds_won[bg], 'active': backgrounds_filter.includes(bg) }" @click="filterBackground(bg)">{{ bg }} ({{ backgrounds_won[bg] || 0 }}) </span>
            </p>
          </div>
          <div class="win-column">
            <p class="win-column-header">By God {{ num_gods_won }}/{{ playable_gods.length }}</p>
            <p>
              <span v-for="god in playable_gods" class="fakelink" :class="{ 'muted': !gods_won[god], 'active': gods_filter.includes(god) }" @click="filterGod(god)">{{ god }} ({{ gods_won[god] || 0 }}) </span>
            </p>
          </div>
        </div>
        <games-table :games="filtered_wins"></games-table>
      </div>
    </div>
  </div>
</template>

<script>
  import AppHeader from '../components/AppHeader'
  import GamesTable from '../components/GamesTable'
  import _ from 'lodash'
  import * as crawl from '../crawl/playable'

  export default {
    components: {
      AppHeader,
      GamesTable
    },
    props: ['player'],
    data: function () {
      return {
        api_loaded: false,
        wins: [],
        last_active: 'Some day',
        num_quits: 15,
        total_playtime: 646,
        species_filter: [],
        backgrounds_filter: [],
        gods_filter: [],
        playable_species: crawl.PLAYABLE_SPECIES,
        playable_backgrounds: crawl.PLAYABLE_BACKGROUNDS,
        playable_gods: crawl.PLAYABLE_GODS
      }
    },
    computed: {
      filtered_wins: function () {
        return _.filter(this.wins, g => {
          if (this.species_filter.length > 0 && !_.includes(this.species_filter, g.species)) return false
          if (this.backgrounds_filter.length > 0 && !_.includes(this.backgrounds_filter, g.background)) return false
          if (this.gods_filter.length > 0 && !_.includes(this.gods_filter, g.god)) return false
          return true
        })
      },
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
      },
      species_won: function () {
        const species = _.groupBy(this.filtered_wins, g => g.species)
        return _.mapValues(species, s => s.length)
      },
      num_species_won: function () {
        return _.intersection(_.keys(this.species_won), _.values(crawl.PLAYABLE_SPECIES)).length
      },
      backgrounds_won: function () {
        const backgrounds = _.groupBy(this.filtered_wins, g => g.background)
        return _.mapValues(backgrounds, b => b.length)
      },
      num_backgrounds_won: function () {
        return _.intersection(_.keys(this.backgrounds_won), _.values(crawl.PLAYABLE_BACKGROUNDS)).length
      },
      gods_won: function () {
        const gods = _.groupBy(this.filtered_wins, g => g.god)
        return _.mapValues(gods, g => g.length)
      },
      num_gods_won: function () {
        return _.intersection(_.keys(this.gods_won), crawl.PLAYABLE_GODS).length
      }
    },
    methods: {
      filterSpecies: function (species) {
        let index = _.indexOf(this.species_filter, species)
        if (index === -1) this.species_filter.push(species)
        else this.species_filter.splice(index, 1)
      },
      filterBackground: function (bg) {
        let index = _.indexOf(this.backgrounds_filter, bg)
        if (index === -1) this.backgrounds_filter.push(bg)
        else this.backgrounds_filter.splice(index, 1)
      },
      filterGod: function (god) {
        let index = _.indexOf(this.gods_filter, god)
        if (index === -1) this.gods_filter.push(god)
        else this.gods_filter.splice(index, 1)
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
