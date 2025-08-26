<script lang="ts">
	import favicon from '$lib/assets/favicon.svg';
	import { fetchData } from '$lib/api';

	let data: any = null;
	let error: string | null = null;

  // Dummy highscores
  let highscores = [
    { user: 'user2', score: 150 },
    { user: 'user1', score: 100 },
    { user: 'user3', score: 80 },
    { user: 'user4', score: 50 }
  ];
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
</svelte:head>

<div class="app-layout">
  <aside class="sidebar">
    <nav>
      <a href="/">Login</a>
      <a href="/game">Spiel</a>
      <a href="/userverwaltung">Userverwaltung</a>
      <a href="/begriffverwaltung">Begriffverwaltung</a>
    </nav>
    <div class="highscores">
      <h3>Highscores</h3>
      <ul>
        {#each highscores as h}
          <li>{h.user}: {h.score}</li>
        {/each}
      </ul>
    </div>
  </aside>
  <main>
    <slot />
  </main>
</div>

<style>
.app-layout {
  display: flex;
  min-height: 100vh;
}
.sidebar {
  width: 220px;
  background: #f5f5f5;
  padding: 20px;
  border-right: 1px solid #ddd;
}
.sidebar nav {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 30px;
}
.sidebar a {
  color: #333;
  text-decoration: none;
  font-weight: bold;
}
.sidebar a:hover {
  text-decoration: underline;
}
.highscores h3 {
  margin: 0 0 10px 0;
}
.highscores ul {
  list-style: none;
  padding: 0;
  margin: 0;
}
main {
  flex: 1;
  padding: 40px;
}
</style>
