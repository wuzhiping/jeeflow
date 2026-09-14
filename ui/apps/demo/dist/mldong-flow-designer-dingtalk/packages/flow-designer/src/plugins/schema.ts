import { FDFormType } from "../types";

/**
 * 开始节点表单元数据
 * 
 */
export const start:FDFormType = {
  labelWidth: '120px',
  formItems: [{
    name: "name",
    label: "唯一编码",
    component: 'Input',
    componentProps: {
      placeholder: '请输入唯一编码'
    }
  },{
    name: "preInterceptors",
    label: "前置拦截器",
    component: 'Input',
    componentProps: {
      placeholder: '请输入前置拦截器'
    }
  }, {
    name: "postInterceptors",
    label: "后置拦截器",
    component: 'Input',
    componentProps: {
      placeholder: '请输入后置拦截器'
    }
  }]
}

/**
 * 结束节点表单元数据
 * 
 */
export const end:FDFormType = {
  labelWidth: '120px',
  formItems: [{
    name: "name",
    label: "唯一编码",
    component: 'Input',
    componentProps: {
      placeholder: '请输入唯一编码'
    }
  }, {
    name: "preInterceptors",
    label: "前置拦截器",
    component: 'Input',
    componentProps: {
      placeholder: '请输入前置拦截器'
    }
  }, {
    name: "postInterceptors",
    label: "后置拦截器",
    component: 'Input',
    componentProps: {
      placeholder: '请输入后置拦截器'
    }
  }]
}

/**
 * 用户任务表单元数据
 * 
 */

export const task:FDFormType = {
  labelWidth: '120px',
  formItems: [{
    name: "name",
    label: "唯一编码",
    component: 'Input',
    componentProps: {
      placeholder: '请输入唯一编码'
    }
  }, {
    name: "displayName",
    label: "显示名称",
    component: 'Input',
    componentProps: {
      placeholder: '请输入显示名称'
    }
  }, {
    name: "preInterceptors",
    label: "前置拦截器",
    component: 'Input',
    componentProps: {
      placeholder: '请输入前置拦截器'
    }
  }, {
    name: "postInterceptors",
    label: "后置拦截器",
    component: 'Input',
    componentProps: {
      placeholder: '请输入后置拦截器'
    }
  }, {
    name: "form",
    label: "表单",
    component: 'Input',
    componentProps: {
      placeholder: '请输入表单'
    }
  }, 
  {
    name: "assignee",
    label: "参与人",
    component: 'Input',
    componentProps: {
      placeholder: '请输入参与人'
    }
  }, {
    name: "assignmentHandler",
    label: "参与人处理类",
    component: 'Input',
    componentProps: {
      placeholder: '请输入参与人处理类'
    }
  }, {
    name: "candidateUsers",
    label: "候选用户",
    component: 'Input',
    helpMessage: '多个用户用英文逗号分隔',
    componentProps: {
      placeholder: '请输入候选用户（多个用逗号分隔）'
    }
  }, {
    name: "candidateGroups",
    label: "候选用户组",
    component: 'Input',
    helpMessage: '多个用户组用英文逗号分隔',
    componentProps: {
      placeholder: '请输入候选用户组（多个用逗号分隔）'
    }
  }, {
    name: "candidateHandler",
    label: "候选用户处理类",
    component: 'Input',
    componentProps: {
      placeholder: '请输入候选用户处理类'
    }
  }, {
    name: "taskType",
    label: "任务类型",
    component: 'Select',
    componentProps: {
      placeholder: '请选择任务类型',
      options: [
        {
          label: '主办',
          value: 'Major'
        },
        {
          label: '协办',
          value: 'Aidant'
        }
      ]
    }
  }, {
    name: "performType",
    label: "参与类型",
    component: 'Select',
    componentProps: {
      placeholder: '请选择参与类型',
      options: [
        {
          label: '普通参与',
          value: 'ANY'
        },
        {
          label: '会签参与',
          value: 'ALL'
        }
      ]
    }
  }, {
    name: "countersignType",
    label: "会签类型",
    component: 'Select',
    defaultValue: 'PARALLEL',
    helpMessage: '参与类型为会签参与时生效',
    componentProps: {
      placeholder: '请选择会签类型',
      options: [
        {
          label: '并行会签',
          value: 'PARALLEL'
        },
        {
          label: '顺序会签',
          value: 'SEQUENTIAL'
        }
      ]
    }
  }, {
    name: "countersignCompletionCondition",
    label: "会签完成条件",
    component: 'Input',
    helpMessage: '参与类型为会签参与时生效，如：nrOfCompletedInstances/nrOfInstances >= 0.6',
    componentProps: {
      placeholder: '请输入会签完成条件'
    }
  }, {
    name: "actionBtns",
    label: "操作按钮",
    component: 'Input',
    helpMessage: [
      '多个按钮用英文逗号分隔，普通参与可选：AGREE(同意)/REJECT(拒绝)/ROLLBACK(退回上一步)/ROLLBACK_TO_OPERATOR(退回发起人)/JUMP(跳转)',
      '会签参与可选：AGREE(同意)/COUNTERSIGN_DISAGREE(会签不同意)/ADD_CANDIDATE(加签)'
    ],
    componentProps: {
      placeholder: '如 AGREE,REJECT,ROLLBACK'
    }
  }, {
    name: "reminderTime",
    label: "提醒时间",
    component: 'Input',
    componentProps: {
      placeholder: '请输入提醒时间'
    }
  }, {
    name: "reminderRepeat",
    label: "重复提醒间隔",
    component: 'Input',
    componentProps: {
      placeholder: '请输入重复提醒间隔'
    }
  }, {
    name: "expireTime",
    label: "期待完成时间",
    component: 'Input',
    componentProps: {
      placeholder: '请输入期待完成时间'
    }
  }, {
    name: "autoExecute",
    label: "是否自动完成",
    component: 'Select',
    componentProps: {
      placeholder: '请选择是否自动完成',
      options: [
        {
          label: '是',
          value: 'Y'
        },
        {
          label: '否',
          value: 'N'
        }
      ]
    }
  }, {
    name: "callback",
    label: "回调处理",
    component: 'Input',
    componentProps: {
      placeholder: '请输入回调处理'
    }
  }]
}
/**
 * 
"expireTime":
"1",
"instanceUrl":
"leaveForm",
"instanceNoClass":
"2",
"preInterceptors":
"3",
"postInterceptors":
"4",
 */
export const process: FDFormType = {
  labelWidth: '130px',
  formItems: [{
    name: "name",
    label: "流程定义唯一编码",
    component: 'Input',
    componentProps: {
      placeholder: '请输入流程定义唯一编码'
    }
  }, {
    name: "displayName",
    label: "流程定义显示名称",
    component: 'Input',
    componentProps: {
      placeholder: '请输入流程定义显示名称'
    }
  },{
    name: "expireTime",
    label: "期望完成时间",
    component: 'Input',
    componentProps: {
      placeholder: '请输入期望完成时间'
    }
  },{
    name: "instanceUrl",
    label: "实例启动表单",
    component: 'Input',
    helpMessage: '如果为元数据表单，数据模型的表名称和流程唯一编码要保持一致',
    componentProps: {
      placeholder: '请输入实例启动表单'
    }
  },{
    name: "enableFieldPerm",
    label: "启用字段权限",
    component: 'Select',
    defaultValue: 0,
    helpMessage: '开启后，可在任务节点配置字段只读/可编辑/不可见',
    componentProps: {
      placeholder: '请选择是否启用字段权限',
      options: [
        {
          label: '否',
          value: 0
        },
        {
          label: '是',
          value: 1
        }
      ]
    }
  },{
    name: "instanceNoClass",
    label: "实例编号生成类",
    component: 'Input',
    componentProps: {
      placeholder: '请输入实例编号生成类'
    }
  },{
    name: "preInterceptors",
    label: "前置拦截器",
    component: 'Input',
    componentProps: {
      placeholder: '请输入前置拦截器'
    }
  }, {
    name: "postInterceptors",
    label: "后置拦截器",
    component: 'Input',
    componentProps: {
      placeholder: '请输入后置拦截器'
    }
  }, {
    name: "relTableName",
    label: "关联业务表",
    component: 'Input',
    helpMessage: '流程结束后业务数据落库的目标表；为空时使用流程唯一编码',
    componentProps: {
      placeholder: '如 biz_leave'
    }
  }, {
    name: "persistMode",
    label: "持久化模式",
    component: 'Select',
    defaultValue: 'ARCHIVE',
    helpMessage: 'ARCHIVE=结束归档（默认）；SYNC=同步演进（发起写入、节点更新、结束定稿）。需配合后置拦截器 PersistPostInterceptor 使用',
    componentProps: {
      placeholder: '请选择持久化模式',
      options: [
        {
          label: '归档',
          value: 'ARCHIVE'
        },
        {
          label: '同步',
          value: 'SYNC'
        }
      ]
    }
  }, {
    name: "selectUserOnInitiate",
    label: "是否发起时选人",
    component: 'Select',
    defaultValue: 0,
    componentProps: {
      placeholder: '请选择是否发起时选人',
      options: [
        {
          label: '否',
          value: 0
        },
        {
          label: '是',
          value: 1
        }
      ]
    }
  }, {
    name: "selectUserApi",
    label: "选人接口地址",
    component: 'Input',
    helpMessage: '发起时选人为"是"时生效；目前仅支持POST请求，和通用下拉接口规范一致',
    componentProps: {
      placeholder: '请输入选人接口地址'
    }
  }, {
    name: "enableCcActors",
    label: "启用抄送人",
    component: 'Select',
    defaultValue: 0,
    componentProps: {
      placeholder: '请选择是否启用抄送人',
      options: [
        {
          label: '否',
          value: 0
        },
        {
          label: '是',
          value: 1
        }
      ]
    }
  }, {
    name: "enableApplyReason",
    label: "启用申请理由",
    component: 'Select',
    defaultValue: 0,
    componentProps: {
      placeholder: '请选择是否启用申请理由',
      options: [
        {
          label: '否',
          value: 0
        },
        {
          label: '是',
          value: 1
        }
      ]
    }
  }, {
    name: "enableAttachment",
    label: "启用附件",
    component: 'Select',
    defaultValue: 0,
    componentProps: {
      placeholder: '请选择是否启用附件',
      options: [
        {
          label: '否',
          value: 0
        },
        {
          label: '是',
          value: 1
        }
      ]
    }
  }]
}
export const subProcess: FDFormType = {
  labelWidth: '130px',
  formItems: [{
    name: "name",
    label: "流程定义唯一编码",
    component: 'Input',
    componentProps: {
      placeholder: '请输入流程定义唯一编码'
    }
  }, {
    name: "displayName",
    label: "流程定义显示名称",
    component: 'Input',
    componentProps: {
      placeholder: '请输入流程定义显示名称'
    }
  },{
    name: "form",
    label: "表单",
    component: 'Input',
    componentProps: {
      placeholder: '请输入表单'
    }
  },{
    name: "version",
    label: "版本号",
    component: 'Input',
    componentProps: {
      placeholder: '请输入版本号'
    }
  },]
}
export const decision: FDFormType = {
  labelWidth: '120px',
  formItems: [{
    name: "name",
    label: "唯一编码",
    component: 'Input',
    componentProps: {
      placeholder: '请输入唯一编码'
    }
  }, {
    name: "expr",
    label: "决策表达式",
    component: 'Input',
    componentProps: {
      placeholder: '请输入决策表达式'
    }
  },{
    name: "handleClass",
    label: "处理类",
    component: 'Input',
    componentProps: {
      placeholder: '请输入处理类'
    }
  },  {
    name: "clazz",
    label: "类路径",
    component: 'Input',
    componentProps: {
      placeholder: '请输入类路径'
    }
  },{
    name: "methodName",
    label: "方法名",
    component: 'Input',
    componentProps: {
      placeholder: '请输入方法名'
    }
  },{
    name: "args",
    label: "参数变量",
    component: 'Input',
    componentProps: {
      placeholder: '请输入参数变量'
    }
  },{
    name: "preInterceptors",
    label: "前置拦截器",
    component: 'Input',
    componentProps: {
      placeholder: '请输入前置拦截器'
    }
  }, {
    name: "postInterceptors",
    label: "后置拦截器",
    component: 'Input',
    componentProps: {
      placeholder: '请输入后置拦截器'
    }
  }]
}
export const fork: FDFormType = {
  labelWidth: '120px',
  formItems: [{
    name: "name",
    label: "唯一编码",
    component: 'Input',
    componentProps: {
      placeholder: '请输入唯一编码'
    }
  }]
}
export const join: FDFormType = {
  labelWidth: '120px',
  formItems: [{
    name: "name",
    label: "唯一编码",
    component: 'Input',
    componentProps: {
      placeholder: '请输入唯一编码'
    }
  }]
}
export const custom: FDFormType = {
  labelWidth: '120px',
  formItems: [{
    name: "name",
    label: "唯一编码",
    component: 'Input',
    componentProps: {
      placeholder: '请输入唯一编码'
    }
  }, {
    name: "displayName",
    label: "显示名称",
    component: 'Input',
    componentProps: {
      placeholder: '请输入显示名称'
    }
  }, {
    name: "clazz",
    label: "类路径",
    component: 'Input',
    componentProps: {
      placeholder: '请输入类路径'
    }
  },{
    name: "methodName",
    label: "方法名",
    component: 'Input',
    componentProps: {
      placeholder: '请输入方法名'
    }
  },{
    name: "args",
    label: "参数变量",
    component: 'Input',
    componentProps: {
      placeholder: '请输入参数变量'
    }
  },{
    name: "preInterceptors",
    label: "前置拦截器",
    component: 'Input',
    componentProps: {
      placeholder: '请输入前置拦截器'
    }
  }, {
    name: "postInterceptors",
    label: "后置拦截器",
    component: 'Input',
    componentProps: {
      placeholder: '请输入后置拦截器'
    }
  }]
}

export const edge: FDFormType = {
  labelWidth: '120px',
  formItems: [{
    name: "name",
    label: "唯一编码",
    component: 'Input',
    componentProps: {
      placeholder: '请输入唯一编码'
    }
  }, {
    name: "displayName",
    label: "显示名称",
    component: 'Input',
    componentProps: {
      placeholder: '请输入显示名称'
    }
    },
    {
      name: "expr",
      label: "表达式",
      component: 'Input',
      componentProps: {
        placeholder: '请输入表达式'
      }
    },
  ]
}