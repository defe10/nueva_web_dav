document.addEventListener("DOMContentLoaded", function () {
    activarChatbot();
    prepararChatVisible();
    scrollInicialOIntercambio();
});

document.addEventListener("click", function (e) {
    const botonNodo = e.target.closest(".mensaje-texto a.btn");
    if (!botonNodo) return;

    window.parent.postMessage({ accion: "cerrar_chatbot" }, "*");
});

function scrollChatToBottom(force = false) {
    const chatBody = document.getElementById("chatbot-body");
    if (!chatBody) return;

    const distanciaDelFondo =
        chatBody.scrollHeight - chatBody.scrollTop - chatBody.clientHeight;

    const estaCercaDelFondo = distanciaDelFondo < 120;

    if (force || estaCercaDelFondo) {
        chatBody.scrollTop = chatBody.scrollHeight;
    }
}

function scrollChatToTopMessage() {
    const chatBody = document.getElementById("chatbot-body");
    if (!chatBody) return;

    chatBody.scrollTop = 0;
}

function scrollInicialOIntercambio() {
    const chatBody = document.getElementById("chatbot-body");
    if (!chatBody) return;

    const mensajesUsuario = chatBody.querySelectorAll(".d-flex.justify-content-end");

    if (!mensajesUsuario.length) {
        chatBody.scrollTop = 0;
        return;
    }

    const ultimoMensajeUsuario = mensajesUsuario[mensajesUsuario.length - 1];

    // 🔥 cálculo relativo al contenedor (NO a la página)
    const offsetTopRelativo =
        ultimoMensajeUsuario.offsetTop - chatBody.offsetTop;

    chatBody.scrollTop = offsetTopRelativo - 12; // margen arriba
}

function prepararChatVisible() {
    const chatBody = document.getElementById("chatbot-body");
    if (!chatBody) return;

    chatBody.classList.remove("chat-ready");

    requestAnimationFrame(() => {
        requestAnimationFrame(() => {
            chatBody.classList.add("chat-ready");
        });
    });
}

function agregarMensajeUsuario(texto) {
    const chatBody = document.getElementById("chatbot-body");
    if (!chatBody) return;

    const userWrapper = document.createElement("div");
    userWrapper.className = "d-flex justify-content-end mb-3 mensaje-fade";
    userWrapper.innerHTML = `
        <div class="user-message">
            <div class="mensaje-texto"></div>
        </div>
    `;

    userWrapper.querySelector(".mensaje-texto").textContent = texto;
    chatBody.appendChild(userWrapper);
}

function agregarTyping() {
    const chatBody = document.getElementById("chatbot-body");
    if (!chatBody) return null;

    const botWrapper = document.createElement("div");
    botWrapper.className = "d-flex mb-3 mensaje-fade js-typing-wrapper";
    botWrapper.innerHTML = `
        <div class="d-flex align-items-start gap-2">
            <div class="chatbot-avatar">DAV</div>
            <div class="bot-message js-typing">
                <div class="typing-indicator">
                    <span></span><span></span><span></span>
                </div>
            </div>
        </div>
    `;

    chatBody.appendChild(botWrapper);
    return botWrapper;
}

function activarChatbot() {
    const links = document.querySelectorAll(".chatbot-option-link");

    links.forEach(link => {
        link.addEventListener("click", function (e) {
            e.preventDefault();

            const url = this.getAttribute("href");
            const texto = this.textContent.trim();
            const container = document.getElementById("chatbot-widget-container");

            agregarMensajeUsuario(texto);
            agregarTyping();
            scrollInicialOIntercambio();

            document.querySelectorAll(".chatbot-option-link").forEach(btn => {
                btn.style.pointerEvents = "none";
                btn.style.opacity = "0.6";
            });

            fetch(url, {
                headers: {
                    "X-Requested-With": "XMLHttpRequest"
                }
            })
                .then(response => response.json())
                .then(data => {
                    setTimeout(() => {
                        container.innerHTML = data.widget_html;
                        activarChatbot();
                        prepararChatVisible();
                        scrollInicialOIntercambio();
                    }, 450);
                })
                .catch(() => {
                    window.location.href = url;
                });
        });
    });

    const navButtons = document.querySelectorAll(".chatbot-nav-btn");

    navButtons.forEach(btn => {
        btn.addEventListener("click", function (e) {
            e.preventDefault();

            const url = this.getAttribute("href");
            const action = this.dataset.chatAction;
            const container = document.getElementById("chatbot-widget-container");

            fetch(url, {
                headers: {
                    "X-Requested-With": "XMLHttpRequest"
                }
            })
                .then(response => response.json())
                .then(data => {
                    container.innerHTML = data.widget_html;
                    activarChatbot();
                    prepararChatVisible();

                    if (action === "inicio") {
                        scrollChatToBottom(true);
                    } else {
                        scrollInicialOIntercambio();
                    }
                })
                .catch(() => {
                    window.location.href = url;
                });
        });
    });

    const form = document.getElementById("chatbot-form");

    if (form) {
        form.addEventListener("submit", function (e) {
            e.preventDefault();

            const input = document.getElementById("chatbot-input");
            const texto = input.value.trim();
            const container = document.getElementById("chatbot-widget-container");

            if (!texto) return;

            agregarMensajeUsuario(texto);
            agregarTyping();
            scrollInicialOIntercambio();

            const formData = new FormData(form);
            input.value = "";

            fetch(form.action || "/chatbot/buscar/", {
                method: "POST",
                body: formData,
                headers: {
                    "X-Requested-With": "XMLHttpRequest"
                }
            })
                .then(response => response.json())
                .then(data => {
                    setTimeout(() => {
                        container.innerHTML = data.widget_html;
                        activarChatbot();
                        prepararChatVisible();
                        scrollInicialOIntercambio();
                    }, 450);
                })
                .catch(() => {
                    alert("Ocurrió un error al procesar la consulta.");
                });
        });
    }
}