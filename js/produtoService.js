import {getData,setData} from './db.js'

export function listar(){
  return getData("produtos")
}