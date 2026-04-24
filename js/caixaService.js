export function registrarVenda(valor, metodo) {
    try {
        const caixa = JSON.parse(localStorage.getItem("caixaAtual"));
        if (!caixa) {
            console.warn("Nenhum caixa aberto.");
            return;
        }
        caixa.entradas.push({ valor, metodo, horario: new Date().toLocaleTimeString() });
        localStorage.setItem("caixaAtual", JSON.stringify(caixa));
    } catch (e) {
        console.error("Erro ao registrar venda no caixa:", e);
    }
}
