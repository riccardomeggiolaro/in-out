export let dataUser = {};

function auth() {
    const token = localStorage.getItem('token');
    if (!token) window.location.href = '/login';
    fetch('/auth/me', {
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

auth();