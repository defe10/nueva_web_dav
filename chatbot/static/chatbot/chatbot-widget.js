document.addEventListener("DOMContentLoaded", function () {
    const toggle = document.getElementById("dav-toggle");
    const panel = document.getElementById("dav-panel");

    if (!toggle || !panel) return;

    const estadoGuardado = localStorage.getItem("dav_abierto");

    if (estadoGuardado === "si") {
        panel.classList.remove("dav-hidden");
    }

    toggle.addEventListener("click", function () {
        panel.classList.toggle("dav-hidden");

        const abierto = !panel.classList.contains("dav-hidden");
        localStorage.setItem("dav_abierto", abierto ? "si" : "no");
    });
});