export async function comRetentativa(operacao, repetir) {
  try {
    return await operacao();
  } catch (e) {
    if (!repetir(e)) throw e;
    console.error('falha transitória, tentando mais uma vez:', e);
    return await operacao();
  }
}
