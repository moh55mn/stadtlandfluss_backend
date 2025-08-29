<script>
  let stadt = '';
  let land = '';
  let fluss = '';
  let tier = '';
  let user = 'user1';
  let buchstabe = 'K';
  let zeit = 60;
  let punktzahl = 100;
  let timerInterval;
  let highscores = [
    { name: 'Anna', score: 120 },
    { name: 'Ben', score: 110 },
    { name: 'Clara', score: 95 }
  ];

  function startGame() {
    punktzahl = 0;
    zeit = 60;
    updateInfo();
    clearInterval(timerInterval);
    timerInterval = setInterval(() => {
      zeit--;
      updateInfo();
      if (zeit <= 0) {
        clearInterval(timerInterval);
        alert('Zeit ist abgelaufen!');
      }
    }, 1000);
  }

  function updateInfo() {
    document.getElementById('info-box').innerHTML = `
      Hallo, ${user}! Das Spiel hat begonnen.<br>
      Buchstabe: <b>${buchstabe}</b> &nbsp; Zeit: <b>${zeit} Sekunden</b> &nbsp; Deine Punktzahl: <b>${punktzahl}</b>
    `;
  }

  function renderHighscores() {
    const table = document.getElementById('highscore-table');
    table.innerHTML = '<tr><th>Name</th><th>Punkte</th></tr>';
    highscores.forEach(entry => {
      table.innerHTML += `<tr><td>${entry.name}</td><td>${entry.score}</td></tr>`;
    });
  }

  window.onload = () => {
    updateInfo();
    renderHighscores();
  };
</script>



<div class="top-bar">
  <div class="info">
    Hallo, {user}! Das Spiel hat begonnen.<br>
    Buchstabe: <b>{buchstabe}</b> &nbsp; Zeit: <b>{zeit} Sekunden</b> &nbsp; Deine Punktzahl: <b>{punktzahl}</b>
  </div>
  <button class="leave-btn">Spiel verlassen</button>
</div>
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
        <td><input type="text" bind:value={stadt} placeholder="Stadt"></td>
        <td><input type="text" bind:value={land} placeholder="Land"></td>
        <td><input type="text" bind:value={fluss} placeholder="Fluss"></td>
        <td><input type="text" bind:value={tier} placeholder="Tier"></td>
      </tr>
    </tbody>
</table>

<style>
.top-bar {
  padding: 10px 20px; background: #f5f5f5; border-bottom: 1px solid #ddd;
  display: flex; align-items: center; justify-content: space-between;
}
.info { font-size: 15px; }
.info b { font-weight: bold; }
.leave-btn {
  background: #888; color: #fff; border: none; padding: 6px 18px; cursor: pointer; font-size: 14px;
}
.leave-btn:hover { background: #666; }
.game-table {
  width: 95%; margin: 30px auto; border-collapse: collapse;
}
.game-table th, .game-table td {
  border: 1px solid #bbb; padding: 8px; text-align: left;
}
.game-table th { background: #eee; }
</style>



<div class="top-bar">
  <div class="info">
    Hallo, {user}! Das Spiel hat begonnen.<br>
    Buchstabe: <b>{buchstabe}</b> &nbsp; Zeit: <b>{zeit} Sekunden</b> &nbsp; Deine Punktzahl: <b>{punktzahl}</b>
  </div>
  <button class="leave-btn">Spiel verlassen</button>
</div>
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
        <td><input type="text" bind:value={stadt} placeholder="Stadt"></td>
        <td><input type="text" bind:value={land} placeholder="Land"></td>
        <td><input type="text" bind:value={fluss} placeholder="Fluss"></td>
        <td><input type="text" bind:value={tier} placeholder="Tier"></td>
      </tr>
    </tbody>
</table>

<style>
.top-bar {
  padding: 10px 20px; background: #f5f5f5; border-bottom: 1px solid #ddd;
  display: flex; align-items: center; justify-content: space-between;
}
.info { font-size: 15px; }
.info b { font-weight: bold; }
.leave-btn {
  background: #888; color: #fff; border: none; padding: 6px 18px; cursor: pointer; font-size: 14px;
}
.leave-btn:hover { background: #666; }
.game-table {
  width: 95%; margin: 30px auto; border-collapse: collapse;
}
.game-table th, .game-table td {
  border: 1px solid #bbb; padding: 8px; text-align: left;
}
.game-table th { background: #eee; }
</style>
