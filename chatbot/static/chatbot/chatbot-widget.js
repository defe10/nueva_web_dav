document.addEventListener("DOMContentLoaded", function () {
    const toggle = document.getElementById("dav-toggle");
    const panel = document.getElementById("dav-panel");

    if (!toggle) return;

    const esMobile = () => window.matchMedia("(max-width: 768px)").matches;

    if (panel && localStorage.getItem("dav_abierto") === "si" && !esMobile()) {
        panel.classList.remove("dav-hidden");
    }

    toggle.addEventListener("click", function () {
        // En móvil: abrir chatbot como página completa
        if (esMobile()) {
            window.location.href = "/chatbot/";
            return;
        }

        // En desktop: abrir/cerrar panel flotante
        if (!panel) return;

        const estabaOculto = panel.classList.contains("dav-hidden");

        if (estabaOculto) {
            panel.classList.remove("dav-hidden");
            localStorage.setItem("dav_abierto", "si");
        } else {
            panel.classList.add("dav-hidden");
            localStorage.setItem("dav_abierto", "no");
        }
    });
});

window.addEventListener("message", function (event) {
    if (event.data?.accion !== "cerrar_chatbot") return;
    if (!window.matchMedia("(max-width: 768px)").matches) return;

    const panel = document.getElementById("dav-panel");
    if (!panel) return;

    panel.classList.add("dav-hidden");
    localStorage.setItem("dav_abierto", "no");
});