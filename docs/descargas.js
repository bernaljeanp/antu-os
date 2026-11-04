"use strict";
(async function () {
  const state = document.getElementById("state");
  try {
    const response = await fetch("https://api.github.com/repos/bernaljeanp/antu-os/releases?per_page=10", {signal: AbortSignal.timeout(12000)});
    if (!response.ok) throw new Error("No se pudieron consultar las versiones.");
    const releases = await response.json();
    const release = releases.find(item => !item.draft && item.assets.some(asset => asset.name === "release.json.sig"));
    if (!release) {
      state.textContent = "La primera entrega con descarga firmada permanente aún no está publicada. Consulta las versiones y la documentación del repositorio.";
      return;
    }
    const asset = release.assets.find(item => item.name === "descargar-antu.py");
    if (!asset || !/^[A-Za-z0-9._-]{1,100}$/.test(release.tag_name)) throw new Error("La publicación no tiene un descargador válido.");
    for (const url of [asset.browser_download_url, release.html_url]) {
      if (!url.startsWith("https://github.com/bernaljeanp/antu-os/")) throw new Error("La publicación tiene un enlace inesperado.");
    }
    document.getElementById("version").textContent = release.tag_name + (release.prerelease ? " · versión de prueba" : "");
    document.getElementById("release-title").textContent = release.name || "Antu OS";
    const download = document.getElementById("download");
    download.href = asset.browser_download_url; download.hidden = false;
    document.getElementById("release-link").href = release.html_url;
    document.getElementById("download-command").textContent = "python descargar-antu.py --tag " + release.tag_name + " --output antu-live.iso";
    document.getElementById("command").hidden = false;
    const parts = release.assets.filter(item => /^antu-live\.iso\.parte-\d+$/.test(item.name));
    const size = parts.reduce((total, part) => total + part.size, 0);
    state.textContent = "Publicada el " + new Date(release.published_at).toLocaleDateString("es-CL") + ". ISO de " + (size / 1e9).toFixed(1) + " GB. Descarga pública, sin cuenta de GitHub.";
  } catch (error) {
    state.textContent = "No se pudo cargar la versión ahora. Usa «Ver versiones y archivos» para consultar la descarga directamente.";
  }
})();
