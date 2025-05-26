export let dataUser = {};

async function auth() {
    const token = localStorage.getItem('token');
    if (!token) window.location.href = '/login';
    await fetch('/api/auth/me', {
        headers: {
            'Authorization': `Bearer ${token}`
        }
    })
    .then(response => response.json())
    .then(data => {
        if (!data.username) {
            localStorage.removeItem('token');
            window.location.href = '/login';
        } else {
            dataUser = data;
        }
    })
    .catch(error => {
        console.error('Error:', error);
    })
}

await auth();