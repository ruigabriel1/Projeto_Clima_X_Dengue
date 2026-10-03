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

