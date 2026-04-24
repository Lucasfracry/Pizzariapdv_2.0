import { getData, setData } from './db.js';

export function listar() {
    return getData("produtos");
}

export function salvar(produto) {
    const produtos = getData("produtos");
    produtos.push(produto);
    setData("produtos", produtos);
}

export function listarPizzas() {
    return getData("produtos").filter(p => p.tipo === "pizza");
}
