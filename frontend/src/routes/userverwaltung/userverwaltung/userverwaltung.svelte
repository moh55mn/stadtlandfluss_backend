<script>
  let isAdmin = true;

  let newUser = '';
  let newRole = 'player';
  let editIndex = -1;

  let users = [
    { username: 'user1', role: 'admin', freigeschaltet: true },
    { username: 'user2', role: 'player', freigeschaltet: false },
    { username: 'user3', role: 'player', freigeschaltet: true }
  ];

  function removeUser(index) {
    if (isAdmin) users = users.filter((_, i) => i !== index);
  }

  function toggleFreigabe(index) {
    if (isAdmin) users[index].freigeschaltet = !users[index].freigeschaltet;
  }

  function saveUser() {
    if (!newUser) return;
    if (editIndex >= 0) {
      users[editIndex].username = newUser;
      users[editIndex].role = newRole;
      editIndex = -1;
    } else {
      users.push({ username: newUser, role: newRole, freigeschaltet: true });
    }
    newUser = '';
    newRole = 'player';
  }

  function editUser(index) {
    newUser = users[index].username;
    newRole = users[index].role;
    editIndex = index;
  }
</script>

<h2>Userverwaltung</h2>

{#if isAdmin}
  <input bind:value={newUser} placeholder="Username" />
  <select bind:value={newRole}>
    <option value="admin">Admin</option>
    <option value="player">Player</option>
  </select>
  <button on:click={saveUser}>{editIndex >= 0 ? 'Ändern' : 'Hinzufügen'}</button>
{/if}

<table>
  <thead>
    <tr>
      <th>Username</th>
      <th>Rolle</th>
      <th>Freigeschaltet</th>
      <th>Aktion</th>
    </tr>
  </thead>
  <tbody>
    {#each users as user, i}
      <tr>
        <td>{user.username}</td>
        <td>{user.role}</td>
        <td>{user.freigeschaltet ? '' : 'x'}</td>
        <td>
          {#if isAdmin}
            <button on:click={() => toggleFreigabe(i)}>Freigabe</button>
            <button on:click={() => editUser(i)}>Bearbeiten</button>
            <button on:click={() => removeUser(i)}>Entfernen</button>
          {/if}
        </td>
      </tr>
    {/each}
  </tbody>
</table>
