<style scoped>
</style>

<template>
  <table class="table table-hover table-striped">
    <thead>
      <tr>
        <th v-for="col in columns">{{ col | columnHeader }}</th>
      </tr>
    </thead>
    <tbody>
      <tr v-for="g in games">
        <td v-for="col in columns">{{ g[col] | columnData(col) }}</td>
      </tr>
    </tbody>
  </table>
</template>

<script>
  export default {
    props: ['games'],
    computed: {
      columns: () => {
        return ['score', 'char', 'god', 'runes', 'turns', 'dur', 'end', 'version']
      }
    }
  }
</script>
