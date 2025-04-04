const originalXHR = window.XMLHttpRequest;
const originalFetch = window.fetch;

// Intercept XMLHttpRequest
window.XMLHttpRequest = function() {
    const xhr = new originalXHR();
    const open = xhr.open;
    const token = localStorage.getItem('token');

    xhr.open = function() {
        const args = arguments;
        open.apply(xhr, args);
        xhr.setRequestHeader('Authorization', `Bearer ${token}`);
    };
    
    return xhr;
};

// Intercept Fetch
window.fetch = function() {
    const args = Array.from(arguments);
    let [url, config = {}] = args;
    const token = localStorage.getItem('token');
    
    config.headers = {
        ...config.headers,
        'Authorization': `Bearer ${token}`
    };
    
    return originalFetch.apply(this, [url, config]);
};