<style scoped>
  .app-header {
    margin-bottom: 1rem;
  }

  .nav-container {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid rgb(190,190,190);
  }

  .nav-item {
    margin-right: 1.5rem;
  }

  .nav-link.active, .nav-link.active:focus, .nav-link:hover, .nav-link.active:hover {
    color: #e29300;
  }
</style>

<template>
  <div class="app-header">
    <img src="/static/images/logo.png" class="m-x-auto d-block"></img>
    <div class="nav-container">
      <nav class="navbar">
        <a class="nav-item nav-link" href="">Home</a>
        <a class="nav-item nav-link" href="">Highscores</a>
        <a class="nav-item nav-link" href="">Win Streaks (beta)</a>
      </nav>
      <form class="form-inline nav navbar">
        <input id="playersearch" class="form-control" type="text" placeholder="Player Search" data-autofirst="True" />
      </form>
    </div>
  </div>
</template>

<script>
  export default {
  }
</script>
