import _ from 'lodash'

export const hours = s => ~~(s / 3600)

export const prettydur = s => {
  let hh = (~~(s / 3600)).toString()
  while (hh.length < 2) hh = '0' + hh
  let mm = (~~(s % 3600 / 60)).toString()
  while (mm.length < 2) mm = '0' + mm
  let ss = (s % 60).toString()
  while (ss.length < 2) ss = '0' + ss
  return `${hh}:${mm}:${ss}`
}

export const date = d => new Date(Number(d) * 1000).toLocaleString()

export const columnHeader = h => {
  switch (h) {
    case 'char':
      return 'Combo'
    case 'dur':
      return 'Duration'
    case 'end':
      return 'Date'
    default:
      return _.capitalize(h)
  }
}

export const columnData = (d, col) => {
  switch (col) {
    case 'dur':
      return prettydur(d)
    case 'end':
      return date(d)
    default:
      return d
  }
}
