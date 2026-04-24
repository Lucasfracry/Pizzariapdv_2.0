import { getData, setData } from './db.js';

console.log("UI.JS CARREGADO - Sistema de Pizzaria Ativo");

// --- FUNÇÃO PARA SALVAR PRODUTO ---
export function salvarProduto() {
    console.log("Tentando salvar produto...");
    const nomeEl = document.getElementById("nome");
    const precoEl = document.getElementById("preco");
    const tipoEl = document.getElementById("tipo");

    if (!nomeEl || !precoEl) {
        console.error("Elementos de input não encontrados no HTML!");
        return;
    }

    const nome = nomeEl.value;
    const preco = Number(precoEl.value);
    const tipo = tipoEl ? tipoEl.value : "pizza";

    if (!nome || !preco) {
        alert("Preencha o nome e o preço corretamente!");
        return;
    }

    const novoProduto = { tipo, nome, preco };
    const produtos = getData("produtos") || [];
    produtos.push(novoProduto);
    setData("produtos", produtos);

    // Limpar campos
    nomeEl.value = "";
    precoEl.value = "";

    console.log("Produto salvo:", novoProduto);
    carregarListaProdutos();
}

// --- FUNÇÃO PARA CARREGAR A LISTA NO FRONT ---
export function carregarListaProdutos() {
    const lista = document.getElementById("listaProdutos");
    if (!lista) return;

    const produtos = getData("produtos") || [];
    lista.innerHTML = "";

    produtos.forEach(p => {
        const div = document.createElement("div");
        div.className = "item";
        div.innerHTML = `<strong>${p.nome}</strong> - R$ ${p.preco.toFixed(2)}`;
        lista.appendChild(div);
    });
}

// --- FUNÇÃO MEIO A MEIO (SEM ALERT/PROMPT DELIRANTE) ---
export function selecionarMeioAMeio() {
    console.log("Botão Meio a Meio clicado");
    const produtos = getData("produtos") || [];
    const pizzas = produtos.filter(p => p.tipo === "pizza" || p.nome.toLowerCase().includes("pizza"));

    if (pizzas.length < 2) {
        alert("Cadastre ao menos 2 pizzas para usar o Meio a Meio!");
        return;
    }

    // Usando prompt apenas para validar a lógica; se funcionar, faremos o modal.
    const s1 = prompt("Digite o nome exato da PRIMEIRA pizza:\nEx: " + pizzas[0].nome);
    const s2 = prompt("Digite o nome exato da SEGUNDA pizza:");

    const p1 = pizzas.find(p => p.nome.toLowerCase() === s1?.toLowerCase());
    const p2 = pizzas.find(p => p.nome.toLowerCase() === s2?.toLowerCase());

    if (p1 && p2) {
        const precoFinal = Math.max(p1.preco, p2.preco);
        const itemCarrinho = {
            nome: `1/2 ${p1.nome} + 1/2 ${p2.nome}`,
            preco: precoFinal,
            quantidade: 1
        };

        const carrinho = getData("carrinho") || [];
        carrinho.push(itemCarrinho);
        setData("carrinho", carrinho);
        
        alert("Pizza Meio a Meio adicionada!");
    } else {
        alert("Um ou mais sabores não foram encontrados. Digite o nome exatamente como cadastrou.");
    }
}

// --- VINCULANDO AO WINDOW PARA O HTML ENXERGAR ---
// Isso é vital para que o onclick="salvarProduto()" funcione!
window.salvarProduto = salvarProduto;
window.selecionarMeioAMeio = selecionarMeioAMeio;
window.carregarListaProdutos = carregarListaProdutos;

// Inicialização
document.addEventListener("DOMContentLoaded", () => {
    carregarListaProdutos();
});