<script>
  let users = Array.from({ length: 40 }, (_, i) => ({
    nr: i + 1,
    username: `user${i + 1}`,
    password: `pass${i + 1}`,
    status: i % 2 === 0 ? 'aktiv' : 'inaktiv'
  }));

  let selectedIndex = null;

  function selectUser(index) {
    selectedIndex = index;
  }

  function createUser() {
    const newNr = users.length + 1;
    users = [...users, {
      nr: newNr,
      username: `user${newNr}`,
      password: `pass${newNr}`,
      status: 'inaktiv'
    }];
  }

  function editUser() {
    if (selectedIndex !== null) {
      users[selectedIndex].username += '_edit';
    }
  }

  function deleteUser() {
    if (selectedIndex !== null) {
      users = users.filter((_, i) => i !== selectedIndex);
      selectedIndex = null;
    }
  }

  function activateUser() {
    if (selectedIndex !== null) {
      users[selectedIndex].status = 'aktiv';
    }
  }
</script>

<h2>Userverwaltung</h2>
<p><strong>Insgesamt:</strong> {users.length} User</p>

<table>
  <thead>
    <tr>
      <th>Nr.</th>
      <th>Username</th>
      <th>Passwort</th>
      <th>Status</th>
    </tr>
  </thead>
  <tbody>
    {#each users as user, i}
      <tr class:selected={selectedIndex === i} on:click={() => selectUser(i)}>
        <td>{user.nr}</td>
        <td>{user.username}</td>
        <td>{user.password}</td>
        <td>{user.status}</td>
      </tr>
    {/each}
  </tbody>
</table>

<div class="button-bar">
  <button on:click={createUser}>Erstellen</button>
  <button on:click={editUser} disabled={selectedIndex === null}>Ändern</button>
  <button on:click={deleteUser} disabled={selectedIndex === null}>Löschen</button>
  <button on:click={activateUser} disabled={selectedIndex === null}>Freischalten</button>
</div>

<style>
table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 20px;
}
th, td {
  border: 1px solid #bbb;
  padding: 8px;
  text-align: left;
}
th {
  background: #eee;
}
tr.selected {
  background-color: #d0ebff;
}
.button-bar {
  margin-top: 30px;
  display: flex;
  justify-content: space-between;
}
button {
  background: #888;
  color: #fff;
  border: none;
  padding: 10px 20px;
  cursor: pointer;
  font-size: 16px;
  border-radius: 6px;
}
button:hover {
  background: #666;
}
button:disabled {
  background: #ccc;
  cursor: not-allowed;
}
</style>

// tenärer Operator Zeile 6
// bearbeitet von Felix Schuler
// 