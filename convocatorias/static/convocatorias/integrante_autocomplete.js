/*
 * Autocompletado en vivo para el paso de integrantes de la postulación.
 *
 * Reemplaza el botón "Buscar" + recarga por un desplegable en vivo. Al elegir
 * una persona del Registro, completa un input oculto con su id y envía el
 * formulario "seleccionar" existente: toda la lógica de vinculación,
 * verificación y documentos sigue viviendo en el backend, sin cambios.
 */
(function () {
  "use strict";

  function debounce(fn, ms) {
    var t;
    return function () {
      var args = arguments, self = this;
      clearTimeout(t);
      t = setTimeout(function () { fn.apply(self, args); }, ms);
    };
  }

  function init(input) {
    if (input.dataset.integranteReady) return;
    input.dataset.integranteReady = "1";

    var url = input.dataset.url;
    var form = document.getElementById(input.dataset.targetForm);
    var hidden = document.getElementById(input.dataset.targetInput);

    var wrap = document.createElement("div");
    wrap.className = "integrante-ac-wrap";
    input.parentNode.insertBefore(wrap, input);
    wrap.appendChild(input);

    var menu = document.createElement("div");
    menu.className = "integrante-ac-menu";
    menu.style.display = "none";
    wrap.appendChild(menu);

    function closeMenu() { menu.style.display = "none"; menu.innerHTML = ""; }

    function pick(item) {
      if (hidden && form) {
        hidden.value = item.id;
        closeMenu();
        form.submit();   // dispara la acción 'seleccionar' del backend
      }
    }

    function render(resultados) {
      menu.innerHTML = "";
      if (!resultados.length) {
        var empty = document.createElement("div");
        empty.className = "integrante-ac-empty";
        empty.textContent =
          "No se encontró a nadie con ese nombre en el Registro Audiovisual.";
        menu.appendChild(empty);
        menu.style.display = "block";
        return;
      }
      resultados.forEach(function (item) {
        var row = document.createElement("div");
        row.className = "integrante-ac-item";
        row.innerHTML =
          '<span class="integrante-ac-label"></span>' +
          '<span class="integrante-ac-meta"></span>';
        row.querySelector(".integrante-ac-label").textContent = item.label;
        row.querySelector(".integrante-ac-meta").textContent = item.sublabel || "";
        row.addEventListener("mousedown", function (e) {
          e.preventDefault();
          pick(item);
        });
        menu.appendChild(row);
      });
      menu.style.display = "block";
    }

    var search = debounce(function () {
      var q = input.value.trim();
      if (q.length < 2) { closeMenu(); return; }
      fetch(url + "?q=" + encodeURIComponent(q), {
        headers: { "X-Requested-With": "XMLHttpRequest" },
      })
        .then(function (r) { return r.json(); })
        .then(function (data) { render(data.resultados || []); })
        .catch(function () { closeMenu(); });
    }, 250);

    input.addEventListener("input", search);
    input.addEventListener("focus", function () {
      if (input.value.trim().length >= 2) search();
    });
    input.addEventListener("blur", function () {
      setTimeout(closeMenu, 150);
    });
  }

  function boot() {
    document
      .querySelectorAll("input[data-integrante-autocomplete]")
      .forEach(init);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
