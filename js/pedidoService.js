import {getData,setData} from './db.js'

export function salvarPedido(p){
  const lista=getData("pedidos")
  lista.push(p)
  setData("pedidos",lista)
}