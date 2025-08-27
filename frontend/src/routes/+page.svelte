<script>
  let username = '';
  let password = '';
  let loginError = '';
  let registerError = '';
  const usernameHelpText = "Erforderlich. 150 Zeichen oder weniger. Nur Buchstaben, Ziffern und @/./+/-/_.";

  import { goto } from '$app/navigation';

  async function login() {
    try {
      //const res = await fetch('https://hanna03re.pythonanywhere.com/api/login', {
      const res = await fetch('https://congenial-giggle-g45p57755747cpgpj-8000.app.github.dev/api/accounts/auth/login/', {
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
    
    // Basic validation
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
        // Show success message before login attempt
        registerError = 'Registrierung erfolgreich! Warte auf Freischaltung durch Admin.';
      } else {
        registerError = data.error || 'Registrierung fehlgeschlagen.';
      }
    } catch (e) {
      registerError = 'Server nicht erreichbar.';
    }
  }
</script>

<div class="login-wrapper">
  <div class="logo-box">
    <img src="/logo.png" alt="Logo" class="logo-img" />
    <div class="title">Stadt Land Fluss</div>
  </div>
  <div class="desc">
    <span>Geben Sie Ihre Anmeldedaten an<br>oder erstellen Sie ein neues Konto</span>
  </div>
  <div class="input-group">
    <input type="text" 
           bind:value={username} 
           placeholder="Username" 
           class="input-large">
    <div class="info-icon" title={usernameHelpText}>?</div>
  </div>
  
  <input type="password" 
         bind:value={password} 
         placeholder="Passwort (mind. 8 Zeichen)" 
         class="input-large">
         
  <button class="btn-large" on:click={login}>Anmelden</button>
  {#if loginError}
    <div class="login-error">{loginError}</div>
  {/if}
  <button class="btn-large" on:click={register}>Registrieren</button>
  {#if registerError}
    <div class="login-error">{registerError}</div>
  {/if}
</div>

<style>
.login-wrapper {
  max-width: 540px;
  margin: 40px auto;
  text-align: center;
}
.logo-box {
  margin-bottom: 20px;
}
.logo-img {
  display: block;
  margin: 0 auto 10px auto;
  width: 220px;
  height: 220px;
  object-fit: cover;
  border-radius: 50%;
  background: #fff;
  box-shadow: 0 2px 16px rgba(0,0,0,0.04);
}
.title {
  font-size: 2.2rem;
  color: #555;
  margin-bottom: 10px;
  font-weight: bold;
  letter-spacing: 1px;
}
.desc {
  font-size: 2.5rem;
  color: #555;
  margin-bottom: 20px;
  line-height: 1.1;
}
.input-large {
  width: 100%;
  font-size: 2rem;
  padding: 16px;
  margin-bottom: 18px;
  box-sizing: border-box;
  border: 2px solid #888;
  border-radius: 4px;
  color: #555;
  background: #fff;
}
.input-large::placeholder {
  color: #bbb;
}
.btn-large {
  width: 100%;
  font-size: 2rem;
  padding: 16px;
  margin-bottom: 18px;
  background: #888;
  color: #fff;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  font-family: inherit;
  transition: background 0.2s;
}
.btn-large:hover {
  background: #666;
}
.login-error {
  color: #c00;
  font-size: 1.3rem;
  margin-bottom: 18px;
}

.input-group {
    position: relative;
    width: 100%;
    margin-bottom: 18px;
  }
  
  .info-icon {
    position: absolute;
    right: 10px;
    top: 50%;
    transform: translateY(-50%);
    width: 20px;
    height: 20px;
    border-radius: 50%;
    background: #888;
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 14px;
    cursor: help;
  }
  
  .input-group .input-large {
    margin-bottom: 0;
    padding-right: 40px;
  }
</style>