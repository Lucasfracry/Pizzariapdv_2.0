import { getData, setData } from './db.js';

export function salvarPedido(pedido) {
    const lista = getData("pedidos");
    pedido.id = Date.now();
    pedido.horario = new Date().toLocaleString();
    lista.push(pedido);
    setData("pedidos", lista);
    return pedido.id;
}

export function listarPedidos() {
    return getData("pedidos");
}
