function auth() {
    fetch('/auth/me', {
        headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
    })
    .then(response => response.json())
    .then(data => {
        console.log(data);
    })
    .catch(error => {
        localStorage.removeItem('token');
        window.location.href = '/login';
    })
}