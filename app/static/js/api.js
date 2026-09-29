export async function fetchStatus() {
  try {
    const r = await fetch("/api/status");
    return await r.json();
  } catch (e) {
    console.error("Erro ao buscar status:", e);
    return null;
  }
}

export async function fetchResultados() {
  try {
    const r = await fetch("/api/resultados");
    const data = await r.json();
    if (data.error) throw new Error(data.error);
    return data;
  } catch (e) {
    console.error("Erro ao buscar resultados:", e);
    return { error: e.message };
  }
}

export function startTraining(modo, codigoIbge, onProgress, onComplete, onError) {
  const body = { modo };
  if (codigoIbge) body.codigo_ibge = codigoIbge;

  fetch("/api/treinar", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  }).then(() => {
    const es = new EventSource("/api/treinar/progresso");
    es.onmessage = (ev) => {
      const data = JSON.parse(ev.data);
      if (data.pct >= 0) onProgress(data);
      if (data.pct >= 100) {
        es.close();
        onComplete();
      }
      if (data.pct === -1) {
        es.close();
        onError(data.msg);
      }
    };
    es.onerror = () => {
      es.close();
      onError("Conexão perdida com o servidor.");
    };
  }).catch((e) => {
    onError(e.message);
  });
}
