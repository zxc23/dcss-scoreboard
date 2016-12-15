<style scoped>
</style>

<template>
  <v-client-table :data="games" :columns="columns" :options="options"></v-client-table>
</template>

<script>
  import * as filters from '../filters/'

  export default {
    props: ['games'],
    computed: {
      columns: () => {
        return ['score', 'char', 'god', 'runes', 'turns', 'dur', 'date', 'version']
      }
    },
    data: function () {
      return {
        options: {
          filterable: false,
          headings: {
            char: 'Combo',
            dur: 'Duration'
          },
          perPage: 20,
          perPageValues: [],
          orderBy: {
            column: 'end'
          },
          templates: {
            score: function (h, row) {
              return row.score.toLocaleString()
            },
            turns: function (h, row) {
              return row.turns.toLocaleString()
            },
            dur: function (h, row) {
              return filters.prettydur(row.dur)
            },
            date: function (h, row) {
              return filters.date(row.end)
            }
          },
          texts: {
            count: 'Showing {from} to {to} of {count} games',
            limit: 'Games:',
            noResults: 'No games match these filters'
          }
        }
      }
    }
  }
</script>
