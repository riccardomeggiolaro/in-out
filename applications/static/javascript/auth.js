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
        if (data.username) {
            console.log(data);
        } else {
            localStorage.removeItem('token');
            window.location.href = '/login';
        }
    })
    .catch(error => {
        console.error('Error:', error);
    })
}

auth();