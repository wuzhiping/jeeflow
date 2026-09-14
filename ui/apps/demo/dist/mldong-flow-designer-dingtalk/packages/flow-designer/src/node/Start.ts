// Start.ts
import { ColorEnum, NodeStateEnum } from "../types/enums";
import { CircleNode, CircleNodeModel } from "@logicflow/core";
class StartModel extends CircleNodeModel {
  setAttributes(): void {
    this.r = 24;
    // 禁止节点拖拽调整大小
    this.resizable = false;
    if((this.text && this.text.value == "") || !this.text) {
      this.text.value = "开始";
    }
    this.text.draggable = false;
    this.text.editable = false;
  }
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  getConnectedTargetRules(): any[] {
    const rules = super.getConnectedTargetRules();
    rules.push({
      message: "开始节点不能是边的目标节点",
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

class StartView extends CircleNode {
 
}

export default {
  type: "start",
  view: StartView,
  model: StartModel,
};
