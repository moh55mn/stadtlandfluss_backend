<script lang="ts">
    import { onMount } from 'svelte';
    import favicon from '$lib/assets/favicon.svg';
    import "../app.css";

    let highscores: { user: string, score: number }[] = [];
    let error: string | null = null;

    onMount(async () => {
        try {
            const res = await fetch('https://fantastic-telegram-pjvg5rrq94f6wgg-8000.app.github.dev/api/game/scoreboard/');
            if (!res.ok) throw new Error('Fehler beim Laden der Highscores');
            const data = await res.json();
            // Map API response to expected format
            highscores = (data.highscores || []).map((entry: any) => ({
                user: entry.user.username,
                score: entry.total_points
            }));
        } catch (e) {
            error = e.message;
        }
    });
</script>

<svelte:head>
    <link rel="icon" href={favicon} />
</svelte:head>

<div class="flex min-h-screen">
    <aside class="card bg-base-200 w-64 p-4 border-r shadow">
        <nav class="flex flex-col gap-2 mb-6">
            <a href="/" class="btn btn-ghost">Login</a>
            <a href="/game" class="btn btn-ghost">Spiel</a>
            <a href="/userverwaltung" class="btn btn-ghost">Userverwaltung</a>
            <a href="/begriffverwaltung" class="btn btn-ghost">Begriffverwaltung</a>
        </nav>
        <div class="card bg-base-100 p-4">
            <h3 class="card-title mb-2">Highscores</h3>
            {#if error}
                <div class="alert alert-error my-2">{error}</div>
            {/if}
            <ul class="list-none p-0 m-0">
                {#each highscores as h}
                    <li class="flex justify-between py-1">
                        <span>{h.user}</span>
                        <span class="badge badge-outline">{h.score}</span>
                    </li>
                {/each}
            </ul>
        </div>
    </aside>
    <main class="flex-1 p-8 bg-base-100">
        <slot />
    </main>
</div>
