import { getData, setData } from './db.js';

export function addItem(item) {
    const carrinho = getData("carrinho");
    carrinho.push(item);
    setData("carrinho", carrinho);
}

export function getCarrinho() {
    return getData("carrinho");
}

export function limpar() {
    setData("carrinho", []);
}

export function getTotal() {
    return getData("carrinho").reduce((t, i) => t + i.preco, 0);
}

export function removerItem(index) {
    const carrinho = getData("carrinho");
    carrinho.splice(index, 1);
    setData("carrinho", carrinho);
}
