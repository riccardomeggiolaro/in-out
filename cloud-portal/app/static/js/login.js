document.getElementById("login-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const errorEl = document.getElementById("login-error");
    errorEl.classList.add("hidden");

    const form = new FormData(event.target);
    try {
        const data = await apiFetch("/api/auth/login", {
            method: "POST",
            body: JSON.stringify({
                username: form.get("username"),
                password: form.get("password"),
            }),
        });
        setToken(data.access_token);
        window.location.href = "/dashboard";
    } catch (e) {
        errorEl.textContent = "Username o password non validi.";
        errorEl.classList.remove("hidden");
    }
});

if (getToken()) {
    window.location.href = "/dashboard";
}
