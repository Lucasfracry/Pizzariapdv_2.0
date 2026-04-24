import { getData, setData } from './db.js';

// --- FUNÇÃO PARA SALVAR PRODUTO ---
export function salvarProduto() {
    const nomeEl = document.getElementById("nome");
    const precoEl = document.getElementById("preco");
    const tipoEl = document.getElementById("tipo");

    if (!nomeEl || !precoEl) return;

    const nome = nomeEl.value.trim();
    const preco = Number(precoEl.value);
    const tipo = tipoEl ? tipoEl.value : "pizza";

    if (!nome || !preco) {
        alert("Preencha o nome e o preço corretamente!");
        return;
    }

    const produto = { tipo, nome, preco };
    const produtos = getData("produtos") || [];
    produtos.push(produto);
    setData("produtos", produtos);

    nomeEl.value = "";
    precoEl.value = "";

    carregarListaProdutos();
    // Se existir a função carregarProdutos (no app.js ou ui.js), chama ela
    if (window.carregarProdutos) window.carregarProdutos();
}

// --- FUNÇÃO PARA CARREGAR A LISTA NO MENU LATERAL ---
export function carregarListaProdutos() {
    const lista = document.getElementById("listaProdutos");
    if (!lista) return;

    const produtos = getData("produtos") || [];
    lista.innerHTML = "";

    produtos.forEach(p => {
        const item = document.createElement("div");
        item.className = "item";
        item.innerHTML = `<strong>${p.nome}</strong> - R$ ${p.preco.toFixed(2)}`;
        lista.appendChild(item);
    });
}

// --- LÓGICA MEIO A MEIO PROFISSIONAL ---
export function selecionarMeioAMeio() {
    const produtos = getData("produtos") || [];
    const pizzas = produtos.filter(p => p.tipo === "pizza" || p.nome.toLowerCase().includes("pizza"));

    if (pizzas.length < 2) {
        alert("Cadastre pelo menos 2 pizzas para fazer Meio a Meio!");
        return;
    }

    // Listagem simples para o prompt
    const menu = pizzas.map((p, i) => `${i + 1}. ${p.nome}`).join("\n");
    const s1 = prompt("Digite o NOME do primeiro sabor:\n\n" + menu);
    const s2 = prompt("Digite o NOME do segundo sabor:");

    const p1 = pizzas.find(p => p.nome.toLowerCase() === s1?.toLowerCase());
    const p2 = pizzas.find(p => p.nome.toLowerCase() === s2?.toLowerCase());

    if (p1 && p2) {
        const precoFinal = Math.max(p1.preco, p2.preco);
        const itemMisto = {
            nome: `1/2 ${p1.nome} + 1/2 ${p2.nome}`,
            preco: precoFinal,
            quantidade: 1
        };

        const carrinho = getData("carrinho") || [];
        carrinho.push(itemMisto);
        setData("carrinho", carrinho);
        
        alert("Pizza Meio a Meio adicionada!");
        if (window.carregarProdutos) window.carregarProdutos();
    } else {
        alert("Sabor não encontrado! Digite o nome exatamente como cadastrado.");
    }
}

// ============================================================
// SOLUÇÃO DO PROBLEMA: VINCULANDO AO WINDOW
// Isso faz o HTML "enxergar" as funções dentro do onclick
// ============================================================
window.salvarProduto = salvarProduto;
window.selecionarMeioAMeio = selecionarMeioAMeio;
window.carregarListaProdutos = carregarListaProdutos;

// Inicialização ao carregar a página
window.onload = carregarListaProdutos;