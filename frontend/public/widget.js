/*!
 * ConsultaSmart — Widget embebible (burbuja flotante).
 *
 * Uso:
 *   <script src="https://<host>/widget.js"
 *           data-tenant-id="rpp"
 *           data-primary-color="#004a87"
 *           data-title="Consultor Experto RPP"
 *           async></script>
 *
 * No reempaqueta la UI del chat (React) por separado: reutiliza la ruta SPA
 * real /widget (ver WidgetPage.jsx), ya probada, dentro de un <iframe> que
 * este script inyecta y controla (botón flotante + panel). Mantener una sola
 * implementación del chat evita que este loader y la app principal se
 * desincronicen con el tiempo.
 */
(function () {
  'use strict';

  if (window.__consultaSmartWidgetLoaded) return;
  window.__consultaSmartWidgetLoaded = true;

  // --- 1. Localizar el <script> propio (para leer su src y sus data-*) -----
  // document.currentScript es fiable incluso con `async` siempre que se lea
  // de forma síncrona en la primera línea de ejecución del script (que es
  // exactamente lo que hacemos aquí). Fallback por si algún navegador viejo
  // ya lo perdió: buscar el último <script> cuyo src contenga "widget.js".
  var thisScript = document.currentScript;
  if (!thisScript) {
    var scripts = document.getElementsByTagName('script');
    for (var i = scripts.length - 1; i >= 0; i--) {
      if (scripts[i].src && scripts[i].src.indexOf('widget.js') !== -1) {
        thisScript = scripts[i];
        break;
      }
    }
  }
  if (!thisScript) {
    console.error('[ConsultaSmart Widget] No se pudo localizar la etiqueta <script> propia; abortando.');
    return;
  }

  var ds = thisScript.dataset || {};
  var tenantId = ds.tenantId || 'general';
  var primaryColor = ds.primaryColor || '#3b82f6';
  var title = ds.title || 'Asistente Virtual';

  // El iframe SIEMPRE apunta al origen real de este script (consulta-smart),
  // sin importar en qué dominio de terceros esté embebido — así el widget es
  // portable a cualquier sitio sin configuración adicional.
  var origin;
  try {
    origin = new URL(thisScript.src).origin;
  } catch (e) {
    console.error('[ConsultaSmart Widget] No se pudo determinar el origen desde src="' + thisScript.src + '"; abortando.');
    return;
  }

  var iframeSrc = origin + '/widget?tenantId=' + encodeURIComponent(tenantId) +
    '&themeColor=' + encodeURIComponent(primaryColor) +
    '&title=' + encodeURIComponent(title);

  // El logo del FAB NO se pasa por atributo (a diferencia de color/título) --
  // se lee directo del perfil configurado en el panel admin (mismo endpoint
  // público que ya usa ChatInterface.jsx), para que quede sincronizado
  // automáticamente sin duplicar la URL del logo en el <script> del sitio
  // embebido. Si el perfil no tiene logo_url, se usa el ícono genérico.
  var logoUrl = null;

  // --- 2. Estilos, con prefijo único para no chocar con el CSS del sitio host ---
  var STYLE_ID = 'consulta-smart-widget-styles';
  if (!document.getElementById(STYLE_ID)) {
    var style = document.createElement('style');
    style.id = STYLE_ID;
    style.textContent = [
      '.csw-fab{position:fixed;bottom:20px;right:20px;width:60px;height:60px;',
      'border-radius:50%;border:none;cursor:pointer;z-index:2147483000;',
      'box-shadow:0 4px 16px rgba(0,0,0,.25);display:flex;align-items:center;',
      'justify-content:center;transition:transform .15s ease;padding:0;}',
      '.csw-fab:hover{transform:scale(1.06);}',
      '.csw-fab svg{width:28px;height:28px;fill:#fff;pointer-events:none;}',
      '.csw-panel{position:fixed;bottom:92px;right:20px;width:380px;height:600px;',
      'max-height:calc(100vh - 112px);border-radius:16px;overflow:hidden;',
      'box-shadow:0 10px 40px rgba(0,0,0,.25);z-index:2147483000;',
      'border:none;opacity:0;transform:translateY(16px);pointer-events:none;',
      'transition:opacity .18s ease,transform .18s ease;background:#fff;}',
      '.csw-panel.csw-open{opacity:1;transform:translateY(0);pointer-events:auto;}',
      '.csw-panel iframe{width:100%;height:100%;border:none;display:block;}',
      '@media (max-width:480px){',
      '.csw-panel{width:100vw;height:100vh;max-height:100vh;bottom:0;right:0;',
      'border-radius:0;}',
      '}',
    ].join('');
    document.head.appendChild(style);
  }

  // --- 3. Botón flotante (FAB) ---------------------------------------------
  var ICON_CHAT = '<svg viewBox="0 0 24 24"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z"/></svg>';
  var ICON_CLOSE = '<svg viewBox="0 0 24 24"><path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/></svg>';

  var fab = document.createElement('button');
  fab.className = 'csw-fab';
  fab.type = 'button';
  fab.setAttribute('aria-label', title);
  fab.style.background = primaryColor;
  fab.innerHTML = ICON_CHAT;

  // --- 4. Panel del chat (el <iframe> se crea recién al primer clic, para ---
  // no gastar la sesión de invitado ni cargar recursos si nunca se abre) ----
  var panel = document.createElement('div');
  panel.className = 'csw-panel';

  var isOpen = false;
  var iframeCreated = false;

  function closedIcon() {
    return logoUrl
      ? '<img src="' + logoUrl + '" alt="" style="width:60%;height:60%;object-fit:cover;border-radius:50%;pointer-events:none;">'
      : ICON_CHAT;
  }

  function openPanel() {
    if (!iframeCreated) {
      var iframe = document.createElement('iframe');
      iframe.src = iframeSrc;
      iframe.title = title;
      iframe.setAttribute('allow', 'clipboard-write');
      panel.appendChild(iframe);
      iframeCreated = true;
    }
    panel.classList.add('csw-open');
    fab.innerHTML = ICON_CLOSE;
    fab.setAttribute('aria-label', 'Cerrar ' + title);
    isOpen = true;
  }

  function closePanel() {
    panel.classList.remove('csw-open');
    fab.innerHTML = closedIcon();
    fab.setAttribute('aria-label', title);
    isOpen = false;
  }

  fab.addEventListener('click', function () {
    if (isOpen) {
      closePanel();
    } else {
      openPanel();
    }
  });

  // --- 5. Montar en el DOM una vez que esté listo --------------------------
  function mount() {
    document.body.appendChild(panel);
    document.body.appendChild(fab);
  }

  if (document.body) {
    mount();
  } else {
    document.addEventListener('DOMContentLoaded', mount);
  }

  // --- 6. Sincronizar el logo con el perfil configurado en el admin --------
  // Fire-and-forget: si falla (red, CORS, perfil sin logo) se queda con el
  // ícono genérico, nunca bloquea el montaje del botón flotante de arriba.
  fetch(origin + '/api/v1/admin/chatbot/profiles')
    .then(function (res) { return res.ok ? res.json() : []; })
    .then(function (profiles) {
      var profile = (profiles || []).filter(function (p) { return p.id === tenantId; })[0];
      if (profile && profile.logo_url) {
        logoUrl = profile.logo_url;
        if (!isOpen) fab.innerHTML = closedIcon();
      }
    })
    .catch(function () {
      // Silencioso a propósito: el widget ya funciona con el ícono genérico.
    });
})();
