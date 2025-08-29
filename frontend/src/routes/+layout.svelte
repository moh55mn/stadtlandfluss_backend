<script lang="ts">
    import { onMount } from 'svelte';
    import favicon from '$lib/assets/favicon.svg';
    import "../app.css";

    let highscores: { user: string, score: number }[] = [];
    let error: string | null = null;
    let sidebarOpen = true;
    let theme = 'custom';

    function toggleSidebar() {
        sidebarOpen = !sidebarOpen;
    }

    function toggleTheme() {
        theme = theme === 'custom' ? 'customDark' : 'custom';
        document.documentElement.setAttribute('data-theme', theme);
    }

    onMount(async () => {
        try {
            const res = await fetch('https://congenial-giggle-g45p57755747cpgpj-8000.app.github.dev/api/game/scoreboard/');
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
    {#if sidebarOpen}
        <aside class="card bg-base-200 w-64 p-4 border-r shadow flex flex-col items-center transition-all duration-300">
            <button class="btn btn-sm btn-square mb-4" on:click={toggleSidebar} aria-label="Sidebar umschalten">
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 12H5"/></svg>
            </button>
            <nav class="flex flex-col gap-2 mb-6 w-full">
                <a href="/" class="btn btn-ghost">Login</a>
                <a href="/game" class="btn btn-ghost">Spiel</a>
                <a href="/userverwaltung" class="btn btn-ghost">Userverwaltung</a>
                <a href="/begriffverwaltung" class="btn btn-ghost">Begriffverwaltung</a>
            </nav>
            <div class="card bg-base-100 p-4 w-full">
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
            <div class="flex-grow"></div>
            <label class="flex cursor-pointer gap-2 mb-2" aria-label="Theme wechseln">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5" /><path d="M12 1v2M12 21v2M4.2 4.2l1.4 1.4M18.4 18.4l1.4 1.4M1 12h2M21 12h2M4.2 19.8l1.4-1.4M18.4 5.6l1.4-1.4" /></svg>
                <input type="checkbox" class="toggle theme-controller" checked={theme === 'customDark'} on:change={toggleTheme} />
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg>
            </label>
        </aside>
    {:else}
        <button class="btn btn-sm btn-square m-4 absolute top-0 left-0 z-10" on:click={toggleSidebar} aria-label="Sidebar anzeigen">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12H19"/></svg>
        </button>
    {/if}
    <main class="min-h-screen flex flex-col w-full">
        <slot />
    </main>
</div>
