import { HtmlResize } from "@logicflow/extension";

class CustomHtmlModel extends HtmlResize.model {
  setAttributes(): void {
    this.text.editable = false
  }
}
class CustomHtmlView extends HtmlResize.view {
  shouldUpdate(): boolean {
    const data = {
      ...this.props.model.getProperties(),
      isSelected: this.props.model.isSelected,
      isHovered: this.props.model.isHovered,
      // id: this.props.model.id,
      // __textValue__: this.props.model.text.value
    }
    if (this.preProperties && this.preProperties === JSON.stringify(data)) return false
    this.preProperties = JSON.stringify(data)
    return true
  }
  // LogicFlow HtmlResizeView 基类签名：rootEl 为 SVGForeignObjectElement，内部按 HTMLElement 使用
  setHtml(rootEl: SVGForeignObjectElement) {
    const root = rootEl as unknown as HTMLElement;
    root.innerHTML = '';
    const el: HTMLElement = document.createElement('div');
    el.style.width = '100%';
    el.style.height = '100%';
    if(this.props.model.isHovered) {
      el.style.background = 'yellow'
    } else {
      el.style.background = 'red'
    }
    el.innerHTML = this.props.model.isHovered+'-'+this.props.model.isSelected+JSON.stringify(this.props.model.properties)
    root.appendChild(el)
  }
  // 自定义 Html 节点无文本渲染，返回 null（与基类签名 preact.JSX.Element | null 兼容）
  getText(): null {
    return null
  }
}
export default {
  type: "custom-html",
  view: CustomHtmlView,
  model: CustomHtmlModel
}