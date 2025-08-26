<script>
  // Dummy user list
  let users = [
    { username: 'user1', role: 'admin' },
    { username: 'user2', role: 'player' },
    { username: 'user3', role: 'player' }
  ];
  function removeUser(index) {
    users = users.filter((_, i) => i !== index);
  }
</script>

<h2>Userverwaltung</h2>
<table>
  <thead>
    <tr>
      <th>Username</th>
      <th>Rolle</th>
      <th>Aktion</th>
    </tr>
  </thead>
  <tbody>
    {#each users as user, i}
      <tr>
        <td>{user.username}</td>
        <td>{user.role}</td>
        <td><button on:click={() => removeUser(i)}>Entfernen</button></td>
      </tr>
    {/each}
  </tbody>
</table>

<style>
table {
  width: 100%; border-collapse: collapse; margin-top: 20px;
}
th, td {
  border: 1px solid #bbb; padding: 8px; text-align: left;
}
th { background: #eee; }
button {
  background: #888; color: #fff; border: none; padding: 6px 12px; cursor: pointer; font-size: 14px;
}
button:hover { background: #666; }
</style>
