const snackbar = document.getElementById("snackbar");
let currentShowSnackbar = null;

function showSnackbar(backgroundColor, color) {
    snackbar.style.backgroundColor = backgroundColor;
    snackbar.style.color = color;
    snackbar.style.animation = "none"; // Reset animazione
    void snackbar.offsetWidth; // Forza il reflow per riavviare l'animazione
    snackbar.style.animation = ""; // Rimuove il reset e permette di riapplicare le animazioni

    snackbar.classList.add("show");

    if (currentShowSnackbar !== null) clearTimeout(currentShowSnackbar);

    currentShowSnackbar = setTimeout(() => {
        snackbar.addEventListener("animationend", function handler(event) {
            if (event.animationName === "fadeout") {
                snackbar.classList.remove("show");
                snackbar.removeEventListener("animationend", handler);
            }
        });
    }, 3000);
}