<script lang="ts">
  import "../../app.css";
  import { onMount } from 'svelte';

  let user: string | null = null;
  let punktzahl: number | null = null;
  let stadt = '';
  let land = '';
  let fluss = '';
  let tier = '';
  let buchstabe = 'K';
  let zeit = 31;
  let error: string | null = null;

  onMount(async () => {
    try {
      const token = localStorage.getItem('access');
      if (!token) throw new Error('Kein Token gefunden');

      // Fetch user score (includes username)
      const scoreRes = await fetch('https://congenial-giggle-g45p57755747cpgpj-8000.app.github.dev/api/game/me/score/', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      if (!scoreRes.ok) throw new Error('Fehler beim Laden der Punktzahl');
      const scoreData = await scoreRes.json();
      user = scoreData.user.username;
      punktzahl = scoreData.total_points;
    } catch (e) {
      error = e.message;
    }
  });

  async function submitGame() {
    try {
      const res = await fetch('/api/game/submit/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          user,
          stadt,
          land,
          fluss,
          tier,
          buchstabe
        })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Fehler beim Senden der Daten');
      punktzahl = data.score; // Update score after submission
    } catch (e) {
      error = e.message;
    }
  }
</script>

<div class="navbar bg-base-200 shadow mb-4 rounded-box px-6 py-3 flex justify-between items-center">
  <div class="text-lg">
    Hallo, {user || 'Gast'}! Das Spiel hat begonnen.<br>
    <span class="badge badge-primary badge-lg mr-2">Buchstabe: {buchstabe}</span>
    <span class="badge badge-secondary badge-lg mr-2">Zeit: {zeit} Sekunden</span>
    <span class="badge badge-accent badge-lg">Deine Punktzahl: {punktzahl ?? '-'}</span>
  </div>
  <button class="btn btn-error btn-sm">Spiel verlassen</button>
</div>

<div class="overflow-x-auto w-full flex justify-center">
  <form on:submit|preventDefault={submitGame} class="w-full max-w-xl">
    <table class="table table-zebra w-full rounded-box shadow">
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
          <td><input type="text" bind:value={stadt} placeholder="Stadt" class="input input-bordered w-full" /></td>
          <td><input type="text" bind:value={land} placeholder="Land" class="input input-bordered w-full" /></td>
          <td><input type="text" bind:value={fluss} placeholder="Fluss" class="input input-bordered w-full" /></td>
          <td><input type="text" bind:value={tier} placeholder="Tier" class="input input-bordered w-full" /></td>
        </tr>
      </tbody>
    </table>
    <button class="btn btn-primary mt-4 w-full" type="submit">Antworten absenden</button>
    {#if error}
      <div class="alert alert-error mt-2">{error}</div>
    {/if}
  </form>
</div>
