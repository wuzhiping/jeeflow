// SubProcess.ts
import { h } from "@logicflow/core";
import { RectResize } from "@logicflow/extension";
import subProcessSvgStr from '../assets/subProcess.svg?raw'
import { parseSvg } from '../tool'
import { ColorEnum, NodeStateEnum } from "../types/enums";
const paths = parseSvg(subProcessSvgStr)
class SubProcessModel extends RectResize.model {
  setAttributes(): void {
    // 允许节点拖拽调整大小
    this.resizable = true;
    if((this.text && this.text.value == "") || !this.text) {
      this.text.value = "子流程";
    }
    // 从 properties 读取宽高，如果没有则设置默认值
    const { width, height } = this.properties as { width?: number | string; height?: number | string };
    const parsedWidth = width !== undefined && width !== null ? Number(width) : NaN;
    const parsedHeight = height !== undefined && height !== null ? Number(height) : NaN;
    if (!isNaN(parsedWidth)) {
      this.width = parsedWidth;
    }
    if (!isNaN(parsedHeight)) {
      this.height = parsedHeight;
    }
    if (!this.width || isNaN(this.width)) {
      this.width = 150;
    }
    if (!this.height || isNaN(this.height)) {
      this.height = 80;
    }
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

class SubProcessView extends RectResize.view {
  private getLabelShape() {
    const { model } = this.props;
    const { x, y, width, height } = model;
    const style = model.getNodeStyle();
    return h(
      "svg",
      {
        x: x - width / 2 + 5,
        y: y - height / 2 + 5,
        width: 25,
        height: 25,
        viewBox: "0 0 1274 1024"
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
  getResizeShape(): any {
    const { model } = this.props;
    const { x, y, width, height, radius } = model;
    const style = model.getNodeStyle();
    return h("g", {}, [
      h("rect", {
        ...style,
        x: x - width / 2,
        y: y - height / 2,
        rx: radius,
        ry: radius,
        width,
        height
      }),
      this.getLabelShape()
    ]);
  }
}

export default {
  type: "subProcess",
  view: SubProcessView,
  model: SubProcessModel,
};
