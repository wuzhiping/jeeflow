
import LogicFlow from '@logicflow/core';
import { DndPanel, Control, Menu } from '@logicflow/extension';
import { Dagre } from "@logicflow/layout";
import StartSvg from './../assets/start.svg'
import UserTaskSvg from './../assets/user-task.svg'
import CustomSvg from './../assets/custom.svg'
import EndSvg from './../assets/end.svg'
import DecisionSvg from './../assets/decision.svg'
import ForkSvg from './../assets/fork.svg'
import JoinSvg from './../assets/join.svg'
import SubProcessSvg from './../assets/subProcess.svg'
import { FDControlItem, FDFormItemType, FDPatternItem } from '../types';
import * as schema from './schema'
import { NodeTypeEnum } from '../types/enums';
LogicFlow.use(DndPanel)
LogicFlow.use(Control)
LogicFlow.use(Menu)
LogicFlow.use(Dagre)
const nodes = import.meta.glob('../node/*.ts',{
  eager: true
})
const edges = import.meta.glob('../edge/*.ts',{
  eager: true
})
class Flow {
  dndPanel:Array<FDPatternItem> = []
  static pluginName = 'flow'
  static defaultEdgeType = 'snaker:transition'
  defaultDndPanel: Array<FDPatternItem>= [
    {
      type: 'start',
      text: '开始',
      label: '开始节点',
      icon: StartSvg,
    },
    {
      type: 'task',
      label: '用户任务',
      text: '用户任务',
      icon: UserTaskSvg
    },
    {
      type: 'custom',
      label: '自定义任务',
      text: '自定义任务',
      icon: CustomSvg
    },
    {
      type: 'decision',
      label: '条件判断',
      text: '条件判断',
      icon: DecisionSvg
    },
    {
      type: 'fork',
      label: '分支',
      text: '分支',
      icon: ForkSvg
    },
    {
      type: 'join',
      label: '合并',
      text: '合并',
      icon: JoinSvg
    },
    {
      type: 'subProcess',
      label: '子流程',
      text: '子流程',
      icon: SubProcessSvg
    },
    {
      type: 'end',
      text: '结束',
      label: '结束节点',
      icon: EndSvg,
    }
  ]
  props: any;
  defaultControl: Array<FDControlItem> = [
    {
      key: 'zoom-out',
      iconClass: 'lf-control-zoomOut',
      title: '缩小流程图',
      text: '缩小',
      sort: 10,
      onClick: () => {
        this.lf.zoom(false);
      },
    },
    {
      key: 'zoom-in',
      iconClass: 'lf-control-zoomIn',
      title: '放大流程图',
      sort: 20,
      text: '放大',
      onClick: () => {
        this.lf.zoom(true);
      },
    },
    {
      key: 'reset',
      iconClass: 'lf-control-fit',
      title: '恢复流程原有尺寸',
      text: '适应',
      sort: 30,
      onClick: () => {
        this.lf.resetZoom();
      },
    },
    {
      key: 'auto-layout',
      iconClass: 'lf-control-auto-layout', // 需要添加对应的CSS类
      title: '自动布局',
      text: '自动布局',
      sort: 35, // 放在适应(30)之后，上一步(40)之前
      onClick: () => {
        // 先应用布局
        this.lf.extension.dagre.layout(this.props.dagreOptions || {});
      }
    },
    {
      key: 'undo',
      iconClass: 'lf-control-undo',
      title: '回到上一步',
      text: '上一步',
      sort: 40,
      onClick: () => {
        this.lf.undo();
      },
    },
    {
      key: 'redo',
      iconClass: 'lf-control-redo',
      title: '移到下一步',
      sort: 50,
      text: '下一步',
      onClick: () => {
        this.lf.redo();
      },
    },
    {
      key: 'clear',
      iconClass: 'lf-control-clear',
      title: '清空画布',
      sort: 60,
      text: '清空',
      onClick: () => {
        this.lf.clearData();
        (this.props.processForm || schema.process)?.formItems?.forEach((item: FDFormItemType)=>{
          delete this.lf.graphModel[item.name]
        })
      }
    },
    {
      key: 'see',
      iconClass: 'lf-control-see',
      title: '查看流程数据',
      sort: 70,
      text: '查看',
      onClick: () => {
        // 弹窗
        this.props.modalRef.value?.show({
          type: 'see',
          graphData: this.lf.getGraphData(),
          lf: this.lf
        })
      }
    },
    {
      key: 'import',
      iconClass: 'lf-control-import',
      title: '导入流程数据',
      sort: 80,
      text: '导入',
      onClick: () => {
        // 弹窗
        this.props.modalRef.value?.show({
          type: 'import',
          lf: this.lf
        })
      }
    },
    {
      key: 'highlight',
      iconClass: 'lf-control-highlight',
      title: '设置高亮数据',
      sort: 80,
      text: '设置高亮',
      onClick: () => {
        // 弹窗
        this.props.modalRef.value?.show({
          type: 'highlight',
          lf: this.lf
        })
      }
    },
    {
      key: 'save',
      iconClass: 'lf-control-save',
      title: '保存流程数据',
      sort: 90,
      text: '保存',
      onClick: () => {
        const { eventCenter } = this.lf.graphModel;
        eventCenter.emit("custom:save", this.lf.getGraphData());
      },
    },
    {
      key: 'fullscreen',
      iconClass: 'lf-control-fullscreen',
      text: '全屏',
      title: '全屏/退出全屏',
      sort: 100,
      onClick: () => {
        // 调用父组件的 toggleFullscreen 方法
        if (this.props.toggleFullscreen && typeof this.props.toggleFullscreen === 'function') {
          this.props.toggleFullscreen();
        }
      }
    }
  ];
  lf: any;
  constructor(data: any){
    this.lf = data.lf;
    const props = data.props
    this.props = props
    // 注册../node/*.ts下的所有节点
    Object.keys(nodes).forEach((key) => {
      const node = (nodes[key] as any).default
      if(props.typePrefix && !node.type.startsWith(props.typePrefix)) {
        node.type = `${props.typePrefix}${node.type}`
      }
      this.lf.register(node)
    })
    // 注册../edge/*.ts下的所有边
    Object.keys(edges).forEach((key) => {
      const edge = (edges[key] as any).default
      if(props.typePrefix && !edge.type.startsWith(props.typePrefix)) {
        edge.type = `${props.typePrefix}${edge.type}`
      }
      this.lf.register(edge)
    })
    // 预览模式时
    if(props.viewer){
      this.lf.extension.menu.setMenuConfig({
        // nodeMenu: [],
        // edgeMenu: []
      })
    } else {
      // 设置右键菜单
      this.lf.extension.menu.setMenuConfig({
        nodeMenu: [
          {
            text: '删除',
            callback: (node: any) => {
              // node为该节点数据
              this.lf.deleteNode(node.id)
            }
          }
        ]
      })
    }
    
    // 拖拽面板追加类型前辍
    this.defaultDndPanel = this.defaultDndPanel.map((item: FDPatternItem) => {
      if(props.typePrefix && item.type && !item.type.startsWith(props.typePrefix)) {
        item.type = `${props.typePrefix}${item.type}`
      }
      return item
    })
    let defaultEdgeType = props.defaultEdgeType || Flow.defaultEdgeType
    if(props.typePrefix && !defaultEdgeType.startsWith(props.typePrefix)){
      defaultEdgeType = `${props.typePrefix}${defaultEdgeType}`
    }
    this.lf.setDefaultEdgeType(defaultEdgeType)
    if(props.initDndPanel !== false && props.viewer !==true) {
      // 如果type相等，则替换属性，否则就追加
      const newDndPanel: Array<FDPatternItem> = [...this.defaultDndPanel]
      if(props.dndPanel && props.dndPanel.length > 0) {
        props.dndPanel.forEach((item: FDPatternItem) => {
          const index = newDndPanel.findIndex((i) => i.type === item.type)
          if(index > -1) {
            if(item.hide === true) {
              // 隐藏，则删除
              newDndPanel.splice(index, 1)
            } else {
              // 覆盖属性
              newDndPanel[index] = {
                ...newDndPanel[index],
                ...item,
              }
            }

          } else {
            newDndPanel.push(item)
          }
        })
      }
      // 对newDndPanel进行排序，以sort属性正序排序
      newDndPanel.sort((a:FDPatternItem, b: FDPatternItem) => {
        return (a.sort === undefined ? 99: a.sort) - (b.sort === undefined ? 99: b.sort)
      })
      this.initDndPanel(newDndPanel)
    }
    if(props.initControl !== false) {
      // 如果key相等，则替换属性，否则就追加
      const newControl: Array<FDControlItem> = [...this.defaultControl]
      if(props.control && props.control.length > 0) {
        props.control.forEach((item: FDControlItem) => {
          const index = newControl.findIndex((i) => i.key === item.key)
          if(index > -1) {
            if(item.hide === true) {
              // 隐藏，则删除
              newControl.splice(index, 1)
            } else {
              // 覆盖属性
              newControl[index] = {
                ...newControl[index],
                ...item,
              }
            }

          } else {
            newControl.push(item)
          }
        })
      }
      // 对newDndPanel进行排序，以sort属性正序排序
      newControl.sort((a:FDControlItem, b: FDControlItem) => {
        return (a.sort === undefined ? 99: a.sort) - (b.sort === undefined ? 99: b.sort)
      })
      this.initControl(newControl.filter(item=>{
        if(props.viewer === true) {
          // 只读模式，隐藏部分操作
          return !['undo','redo','clear','see','import','highlight','save'].includes(item.key as any)
        }
        return true
      }))
    } else {
      this.lf.extension.control.controlItems = []
    }
    const lf = this.lf;
    lf.adapterIn = (userData: any) =>{
      // 绑定name和displayName到graphModel
      // lf.graphModel.name = userData.name
      // lf.graphModel.displayName = userData.displayName
      (props.processForm || schema.process)?.formItems?.forEach((item: FDFormItemType)=>{
        lf.graphModel[item.name] = userData[item.name]
      })
      return userData;
    }
    lf.adapterOut = (userData: any) =>{
      // console.log('adapterOut', userData)
      // 从graphModel取出name和displayName
      const processData : any= {};
      (props.processForm || schema.process)?.formItems?.forEach((item: FDFormItemType)=>{
        if(Object.keys(lf.graphModel).includes(item.name)){
          processData[item.name] = lf.graphModel[item.name]
        }
      })
      return {
        ...userData,
        ...processData
      };
    }
    lf.graphModel.props = props;
    // 事件处理优先级：dndPanel.nodeClick>props.nodeClick>defaultNodeClick
    const { eventCenter } = lf.graphModel;
    // 节点事件
    eventCenter.on('node:click', (event: any) => {
      if(props.viewer === true) {
        return
      }
      const shapeList = this.dndPanel
      const index = shapeList.findIndex((item: FDPatternItem)=>item.type === event.data.type)
      let nodeClick = props.nodeClick
      if(index>=-1) {
        nodeClick = shapeList[index]?.nodeClick || props.nodeClick
      }
      const nodeEventParams = {
        ...event,
        patternItem: shapeList[index],
        lf
      }
      if(nodeClick && typeof nodeClick === 'function') {
        nodeClick(nodeEventParams)
      } else {
        props.drawerRef.value?.show(nodeEventParams)
      }
    })
    // 边事件
    eventCenter.on('edge:click', (event: any) => {
      if(props.viewer === true) {
        return
      }
      let edgeClick = props.edgeClick
      const edgeEventParams = {
        ...event,
        patternItem: {
          form: props.edgeForm || schema.edge
        },
        lf
      }
      if(edgeClick && typeof edgeClick === 'function') {
        edgeClick(edgeEventParams)
      } else {
        props.drawerRef.value?.show(edgeEventParams)
      }
    })
    // 画布事件
    eventCenter.on('blank:contextmenu', (event: any) =>{
      if(props.viewer === true) {
        return
      }
      const processData : any= {};
      (props.processForm || schema.process)?.formItems?.forEach((item: FDFormItemType)=>{
        if(Object.keys(lf.graphModel).includes(item.name)){
          processData[item.name] = lf.graphModel[item.name]
        }
      })
      const eventParams = {
        ...event,
        data: {
          type: 'process',
          properties: processData
        },
        patternItem: {
          form: props.processForm || schema.process
        },
        lf
      }
      if(props.blankContextmenu && typeof props.blankContextmenu === 'function') {
        props.blankContextmenu(eventParams)
      } else {
        props.drawerRef.value?.show(eventParams)
      }
    })
  }
  initDndPanel(data: any){
    this.lf.extension.dndPanel.setPatternItems(data)
    this.dndPanel = data || []
    this.dndPanel.forEach(item=>{
      if(item.type && !item.form) {
        let type: NodeTypeEnum = item.type as NodeTypeEnum
        if(this.props.typePrefix) {
          type = type.replace(this.props.typePrefix, '') as NodeTypeEnum
        }
        item.form = schema[type]
      }
    })
  }
  initControl(data: any){
    this.lf.extension.control.controlItems = data || []
  }
}
export default Flow