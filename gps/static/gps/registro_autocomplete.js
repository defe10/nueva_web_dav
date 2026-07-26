/*
 * Autocompletado de vínculo con el Registro Audiovisual.
 *
 * Se engancha a cada <input data-registro-autocomplete> (Dirección / Producción).
 * Mientras se escribe, consulta el endpoint data-registro-url y ofrece las
 * coincidencias. Al elegir una, completa el campo oculto "<name>_ref" con
 * "ct:id" (el vínculo). Si se sigue editando el texto, el vínculo se limpia:
 * un nombre no registrado queda simplemente como texto libre.
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
    if (input.dataset.registroReady) return;
    input.dataset.registroReady = "1";

    var url = input.dataset.registroUrl;
    var hidden = document.getElementById(input.id + "_ref");

    // Contenedor posicionado para colgar el menú de resultados.
    var wrap = document.createElement("div");
    wrap.className = "registro-ac-wrap";
    input.parentNode.insertBefore(wrap, input);
    wrap.appendChild(input);

    var menu = document.createElement("div");
    menu.className = "registro-ac-menu";
    menu.style.display = "none";
    wrap.appendChild(menu);

    function closeMenu() { menu.style.display = "none"; menu.innerHTML = ""; }

    function clearLink() { if (hidden) hidden.value = ""; }

    function pick(item) {
      input.value = item.label;
      if (hidden) hidden.value = item.ct + ":" + item.id;
      closeMenu();
    }

    function render(resultados) {
      menu.innerHTML = "";
      if (!resultados.length) { closeMenu(); return; }
      resultados.forEach(function (item) {
        var row = document.createElement("div");
        row.className = "registro-ac-item";
        row.innerHTML =
          '<span class="registro-ac-label"></span>' +
          '<span class="registro-ac-meta"></span>';
        row.querySelector(".registro-ac-label").textContent = item.label;
        row.querySelector(".registro-ac-meta").textContent =
          item.tipo + (item.sublabel ? " · " + item.sublabel : "");
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

    input.addEventListener("input", function () {
      clearLink();   // al editar, se rompe cualquier vínculo previo
      search();
    });
    input.addEventListener("focus", function () {
      if (input.value.trim().length >= 2) search();
    });
    input.addEventListener("blur", function () {
      // Pequeño retardo para permitir el mousedown de un item.
      setTimeout(closeMenu, 150);
    });
  }

  function boot() {
    document
      .querySelectorAll("input[data-registro-autocomplete]")
      .forEach(init);
  }

  // Para inicializar inputs agregados dinámicamente (p. ej. filas de créditos).
  window.registroAutocompleteInit = boot;

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
