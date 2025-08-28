<script>
  import HighscoreTable from './HighscoreTable.svelte';

  let stadt = '';
  let land = '';
  let fluss = '';
  let tier = '';
  let user = 'user1';
  let buchstabe = 'K';
  let zeit = 60;
  let punktzahl = 0;
  let timer;
  let isRunning = false;

  function startGame() {
    punktzahl = 0;
    zeit = 60;
    isRunning = true;
    clearInterval(timer);
    timer = setInterval(() => {
      zeit--;
      if (zeit <= 0) {
        clearInterval(timer);
        isRunning = false;
        alert('Zeit ist abgelaufen!');
      }
    }, 1000);
  }
</script>

<div class="top-bar">
  <div class="info">
    Hallo, {user}!<br>
    Buchstabe: <b>{buchstabe}</b> &nbsp; Zeit: <b>{zeit} Sekunden</b> &nbsp; Punktzahl: <b>{punktzahl}</b>
  </div>
  <button on:click={startGame} disabled={isRunning}>Start</button>
</div>

<div class="game-container">
  <table class="game-table">
    <thead>
      <tr>
        <th>Stadt</th>
        <th>Land</th>
        <th>Fluss</th>
        <th>Tier</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td><input bind:value={stadt} placeholder="Stadt" /></td>
        <td><input bind:value={land} placeholder="Land" /></td>
        <td><input bind:value={fluss} placeholder="Fluss" /></td>
        <td><input bind:value={tier} placeholder="Tier" /></td>
      </tr>
    </tbody>
  </table>

  <HighscoreTable />
</div>

<style>
  .top-bar {
    display: flex;
    justify-content: space-between;
    margin-bottom: 1rem;
  }
  .game-container {
    display: flex;
    gap: 2rem;
  }
  .game-table {
    border-collapse: collapse;
    width: 60%;
  }
  .game-table th, .game-table td {
    border: 1px solid #ccc;
    padding: 0.5rem;
  }
</style>
