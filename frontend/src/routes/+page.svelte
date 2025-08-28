<script>
  import "../app.css";
  let username = '';
  let password = '';
  let loginError = '';
  let registerError = '';
  const usernameHelpText = "Erforderlich. 150 Zeichen oder weniger. Nur Buchstaben, Ziffern und @/./+/-/_.";

  import { goto } from '$app/navigation';

  async function login() {
    try {
      const res = await fetch('https://fantastic-telegram-pjvg5rrq94f6wgg-8000.app.github.dev/api/accounts/auth/login/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      });
      const data = await res.json();
      if (res.ok && data.access) {
        goto('/game');
      } else {
        loginError = data.error || 'Login fehlgeschlagen.';
      }
    } catch (e) {
      loginError = 'Server nicht erreichbar.';
    }
  }

  async function register() {
    registerError = '';
    if (password.length < 8) {
      registerError = 'Passwort muss mindestens 8 Zeichen lang sein.';
      return;
    }
    try {
      const res = await fetch('https://congenial-giggle-g45p57755747cpgpj-8000.app.github.dev/api/accounts/auth/register/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      });
      const data = await res.json();
      if (res.ok) {
        registerError = 'Registrierung erfolgreich! Warte auf Freischaltung durch Admin.';
      } else {
        registerError = data.error || 'Registrierung fehlgeschlagen.';
      }
    } catch (e) {
      registerError = 'Server nicht erreichbar.';
    }
  }
</script>

<div class="flex flex-col items-center justify-center min-h-screen bg-base-200">
  <div class="card w-full max-w-md shadow-xl bg-base-100">
    <div class="card-body flex flex-col items-center">
      <div class="flex flex-col items-center mb-4">
        <img src="/logo.png" alt="Logo" class="w-32 h-32 rounded-full bg-white shadow" />
        <div class="text-3xl font-bold text-primary mt-2 mb-2">Stadt Land Fluss</div>
        <div class="text-lg text-base-content mb-4 text-center">
          Geben Sie Ihre Anmeldedaten an<br>oder erstellen Sie ein neues Konto
        </div>
      </div>
      <div class="flex flex-col items-center w-full">
        <div class="form-control mb-4 w-full max-w-xs">
          <label class="input input-bordered flex items-center gap-2 w-full">
            <input type="text"
                   bind:value={username}
                   placeholder="Username"
                   class="grow" />
            <span class="tooltip tooltip-left" data-tip={usernameHelpText}>?</span>
          </label>
        </div>
        <div class="form-control mb-4 w-full max-w-xs">
          <input type="password"
                 bind:value={password}
                 placeholder="Passwort (mind. 8 Zeichen)"
                 class="input input-bordered w-full" />
        </div>
        <div class="form-control mb-2 w-full max-w-xs">
          <button class="btn btn-primary w-full" on:click={login}>Anmelden</button>
        </div>
        {#if loginError}
          <div class="alert alert-error my-2 w-full max-w-xs">{loginError}</div>
        {/if}
        <div class="form-control mb-2 w-full max-w-xs">
          <button class="btn btn-secondary w-full" on:click={register}>Registrieren</button>
        </div>
        {#if registerError}
          <div class="alert alert-warning my-2 w-full max-w-xs">{registerError}</div>
        {/if}
      </div>
    </div>
  </div>
</div>