// Decision.ts
import { ColorEnum, NodeStateEnum } from "../types/enums";
import { DiamondNode, DiamondNodeModel, h } from "@logicflow/core";
import decisionQSvgStr from '../assets/decision-cha.svg?raw'
import { parseSvg } from '../tool'
const paths = parseSvg(decisionQSvgStr)
class DecisionModel extends DiamondNodeModel {
  setAttributes(): void {
    this.text.value = "";
    this.rx = 28;
    this.ry = 28;
    this.text.draggable = false;
    this.text.editable = false;
    // 禁止节点拖拽调整大小
    this.resizable = false;
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

class DecisionView extends DiamondNode {
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
  type: "decision",
  view: DecisionView,
  model: DecisionModel,
};
