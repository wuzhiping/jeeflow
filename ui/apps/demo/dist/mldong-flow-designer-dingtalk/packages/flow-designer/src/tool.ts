/**
 * 解析svg字符串，获取path中的d属性值
 */
export const parseSvg = (svgStr: string) => {
  const parser = new DOMParser()
  const svgDoc = parser.parseFromString(svgStr, 'image/svg+xml')
  const svgElements = svgDoc.getElementsByTagName('path')
  const paths = []
  // 遍历svgElements，获取path中的d属性值
  for (let i = 0; i < svgElements.length; i++) {
    const path = svgElements[i]
    const d = path.getAttribute('d')
    if (d) {
      paths.push(d)
    }
  }
  return paths
}