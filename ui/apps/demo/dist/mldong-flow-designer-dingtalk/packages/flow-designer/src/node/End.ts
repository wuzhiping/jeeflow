// End.ts
import { ColorEnum, NodeStateEnum } from "../types/enums";
import { CircleNode, CircleNodeModel, h } from "@logicflow/core";
import endQSvgStr from '../assets/end-q.svg?raw'
import { parseSvg } from '../tool'
const paths = parseSvg(endQSvgStr)
class EndModel extends CircleNodeModel {
  setAttributes(): void {
    this.r = 24;
    // 禁止节点拖拽调整大小
    this.resizable = false;
    if((this.text && this.text.value == "") || !this.text) {
      this.text.value = "结束";
    }
    if(this.text) {
      this.text.x = this.x
      this.text.y = this.y + this.height / 2 + 12
    }
    this.text.draggable = false;
    this.text.editable = false;
  }
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  getConnectedSourceRules(): any[] {
    const rules = super.getConnectedSourceRules();
    rules.push({
      message: "结束节点不能是边的开始节点",
      validate: () => false
    });
    return rules;
  }
  getNodeStyle() {
    const theme = this.graphModel.props.theme;
    const style = super.getNodeStyle();
    if(this.properties.state == NodeStateEnum.history) {
      style.stroke = theme.historyColor || ColorEnum.historyColor;
    } else if(this.properties.state == NodeStateEnum.active) {
      style.stroke = theme.activeColor || ColorEnum.activeColor;
    } else {
      style.stroke = theme.primaryColor || ColorEnum.primaryColor;
    }
    // style.strokeDasharray = "3 3";
    return style;
  }
}

class EndView extends CircleNode {
  private getLabelShape() {
    const { model } = this.props;
    const { x, y} = model;
    const style = model.getNodeStyle();
    const innerWH = 20;
    return h(
      "svg",
      {
        x: x - innerWH/2,
        y: y - innerWH/2,
        width: innerWH,
        height: innerWH,
        viewBox: "0 0 1024 1024"
      },
      ...paths.map(d=>{
        return h("path", {
          fill: style.stroke,
          d
        })
      }),
    );
  }

 /**
   * 完全自定义节点外观方法
   */
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  getShape(): any {
  const outCircle = super.getShape();
  return h("g", {}, [
    outCircle,
    this.getLabelShape()
  ]);
}
}

export default {
  type: "end",
  view: EndView,
  model: EndModel,
};
