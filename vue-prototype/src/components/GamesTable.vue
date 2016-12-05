<style scoped>
</style>

<template>
  <v-client-table :data="games" :columns="columns" :options="options"></v-client-table>
</template>

<script>
  export default {
    components: {
    },
    props: ['games'],
    data: function () {
      return {
        options: {
          filterable: false,
          headings: {
            char: 'Combo',
            tmsg: 'End',
            dur: 'Duration'
          },
          perPage: 20,
          perPageValues: [],
          orderBy: {
            column: 'end'
          },
          templates: {
            dur: function (h, row) {
              let dur = row.dur
              let hh = (~~(dur / 3600)).toString()
              while (hh.length < 2) hh = '0' + hh
              let mm = (~~(dur % 3600 / 60)).toString()
              while (mm.length < 2) mm = '0' + mm
              let ss = (dur % 60).toString()
              while (ss.length < 2) ss = '0' + ss
              return `${hh}:${mm}:${ss}`
            },
            date: function (h, row) {
              return new Date(Number(row.end) * 1000).toLocaleString()
            }
          }
        }
      }
    },
    computed: {
      columns: () => {
        return ['score', 'char', 'god', 'runes', 'turns', 'dur', 'date', 'version']
      }
    }
  }
</script>
