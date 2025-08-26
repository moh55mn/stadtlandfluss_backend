import axios from 'axios';

export async function fetchData() {
  const res = await axios.get('https://hanna03re.pythonanywhere.com/api/hello');
  return res.data;
}