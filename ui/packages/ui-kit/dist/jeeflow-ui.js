import { defineComponent as q, reactive as Ue, inject as Ft, computed as E, watch as be, openBlock as o, createElementBlock as u, toDisplayString as w, createCommentVNode as M, Fragment as G, renderList as le, normalizeStyle as ce, createElementVNode as t, createTextVNode as ee, provide as jn, ref as b, onMounted as he, onBeforeUnmount as We, createBlock as ae, Teleport as ht, withModifiers as Se, normalizeClass as ne, renderSlot as ke, createVNode as J, unref as H, withCtx as te, resolveComponent as Zn, createSlots as el, mergeProps as ft, resolveDynamicComponent as Mt, nextTick as tt, Transition as Nt, useCssVars as tl, createStaticVNode as nl, withDirectives as de, vModelText as Te, vShow as Ye, withKeys as st, vModelSelect as ll } from "vue";
const Ke = {
  APPLY: 0,
  // 发起申请
  AGREE: 1,
  // 同意
  REJECT: 2,
  // 拒绝（流程直接结束）
  ROLLBACK: 3,
  // 退回上一步
  JUMP: 4,
  // 跳转指定节点（需 taskName）
  RE_APPLY: 5,
  // 重新提交
  ROLLBACK_TO_OPERATOR: 6,
  // 退回发起人
  COUNTERSIGN_DISAGREE: 20
  // 会签拒绝
}, wc = {
  DOING: 10,
  // 进行中
  FINISHED: 20,
  // 已完成
  WITHDRAW: 30,
  // 已撤回
  INTERRUPT: 40,
  // 强行终止
  PENDING: 50,
  // 挂起
  ABANDON: 99
  // 已废弃
}, _c = {
  NORMAL: 0,
  // 普通（多人任一完成即可）
  COUNTERSIGN: 1
  // 会签（每人独立任务，全部完成才推进）
}, Cc = {
  PARALLEL: "PARALLEL",
  // 并行会签
  SEQUENTIAL: "SEQUENTIAL",
  // 串行会签
  RATIO: "RATIO"
  // 阈值会签
};
class zt extends Error {
  constructor(l, i) {
    super(i), this.code = l;
  }
}
function al(e) {
  const l = () => (typeof e.baseUrl == "function" ? e.baseUrl() : e.baseUrl).replace(/\/+$/, ""), i = e.fetchImpl ?? fetch;
  async function n(a, r = {}) {
    var j, g;
    const y = { ...r };
    "operator" in y || (y.operator = e.getOperator()), (j = e.onRequest) == null || j.call(e, a, y);
    const v = { "Content-Type": "application/json" }, h = (g = e.getToken) == null ? void 0 : g.call(e);
    h && (v.Authorization = `Bearer ${h}`);
    let p;
    try {
      p = await i(`${l()}/wf/${a}`, {
        method: "POST",
        headers: v,
        body: JSON.stringify(y)
      });
    } catch (C) {
      throw new zt(-1, `网络错误：${C.message}`);
    }
    let f;
    try {
      f = await p.json();
    } catch {
      throw new zt(p.status, `非 JSON 响应（HTTP ${p.status}）`);
    }
    if (f.code !== 0) throw new zt(f.code, f.msg || "请求失败");
    return f.data;
  }
  function s(a) {
    return e.hasPermission ? e.hasPermission(a) : !0;
  }
  const c = {
    /** 底层调用（自定义 action 扩展用） */
    flow: n,
    // ═══ 流程定义（7 action）═══
    processDefine: {
      page: (a = {}) => n("processDefine/page", a),
      detail: (a) => n("processDefine/detail", { id: a }),
      startAndExecute: (a, r = {}) => n("processDefine/startAndExecute", {
        processDefineId: a,
        ...r
      }),
      /** 发布流程定义：流程 JSON 顶层展开（对齐 vben5；字符串 content 兼容） */
      deploy: (a) => n(
        "processDefine/deploy",
        typeof a == "string" ? { content: a } : { ...a }
      ),
      /** 重新发布：流程 JSON 顶层展开（对齐 vben5；字符串 content 兼容） */
      redeploy: (a, r) => n(
        "processDefine/redeploy",
        typeof r == "string" ? { processDefineId: a, content: r } : { processDefineId: a, ...r }
      ),
      remove: (a) => n("processDefine/remove", Array.isArray(a) ? { ids: a } : { id: a }),
      upAndDown: (a, r) => n(
        "processDefine/upAndDown",
        Array.isArray(a) ? { ids: a, state: r } : { id: a, state: r }
      ),
      getLastByName: (a) => n("processDefine/getLastByName", { processDefineName: a })
    },
    // ═══ 流程实例（11 action）═══
    processInstance: {
      page: (a = {}) => n("processInstance/page", a),
      detail: (a) => n("processInstance/detail", { id: a }),
      startAndExecute: (a, r = {}) => n("processInstance/startAndExecute", {
        processDefineId: a,
        ...r
      }),
      withdraw: (a) => n("processInstance/withdraw", { id: a }),
      bizData: (a) => n("processInstance/bizData", { processInstanceId: a }),
      highLight: (a) => n("processInstance/highLight", { id: a }),
      approvalRecord: (a) => n("processInstance/approvalRecord", { id: a }),
      getAssigneeTextData: (a, r = !0) => n("processInstance/getAssigneeTextData", { id: a, includeNodeName: r }),
      createCCInstance: (a, r) => n("processInstance/createCCInstance", { processInstanceId: a, actorIds: r }),
      updateCCStatus: (a) => n("processInstance/updateCCStatus", { processInstanceId: a }),
      ccList: (a = {}) => n("processInstance/ccList", a),
      /** 指标卡统计（issues/103 v1.1；全局口径不带 operator 过滤；登录即可） */
      statsOverview: (a = {}) => n("processInstance/stats/overview", a),
      /** 时间趋势：start/end 必填（yyyy-MM-dd HH:mm:ss），连续桶补 0 */
      statsTrend: (a) => n("processInstance/stats/trend", a),
      /** 维度分组：9 个纯列 dimension，Top N 降序；stuckNode/stuckApprover 实时快照忽略 start/end */
      statsGroup: (a) => n("processInstance/stats/group", a)
    },
    // ═══ 流程任务（9 action）═══
    processTask: {
      todoList: (a = {}) => n("processTask/todoList", a),
      doneList: (a = {}) => n("processTask/doneList", a),
      execute: (a, r, y = {}) => n("processTask/execute", { processTaskId: a, submitType: r, ...y }),
      detail: (a) => n("processTask/detail", { id: a }),
      jumpAbleTaskNameList: (a) => n("processTask/jumpAbleTaskNameList", { processInstanceId: a }),
      candidatePage: (a, r = {}) => n("processTask/candidatePage", { processTaskId: a, ...r }),
      surrogate: (a, r) => n("processTask/surrogate", { processTaskId: a, actorIds: r }),
      addCandidate: (a, r) => n("processTask/addCandidate", { processTaskId: a, actorIds: r }),
      latest: (a) => n("processTask/latest", { processInstanceId: a })
    },
    // ═══ 流程设计（9 action）═══
    processDesign: {
      page: (a = {}) => n("processDesign/page", a),
      detail: (a) => n(
        "processDesign/detail",
        { id: a }
      ),
      save: (a) => n("processDesign/save", a),
      update: (a, r) => n("processDesign/update", { id: a, ...r }),
      /** 保存设计稿：流程 JSON 顶层展开（对齐 vben5 契约；字符串 content 兼容） */
      updateDefine: (a, r) => n(
        "processDesign/updateDefine",
        typeof r == "string" ? { processDesignId: a, content: r } : { processDesignId: a, ...r }
      ),
      remove: (a) => n("processDesign/remove", Array.isArray(a) ? { ids: a } : { id: a }),
      deploy: (a) => n("processDesign/deploy", { id: a }),
      redeploy: (a) => n("processDesign/redeploy", { id: a }),
      /** 按类型分组（返回 Map<type, items>；boot3 前端转换见 guide） */
      listByType: () => n("processDesign/listByType"),
      /** listByType 的 boot3 形态（[{type,title,items}]），与参考实现转发层一致 */
      listByTypeAsArray: async () => {
        const a = await c.processDesign.listByType();
        return Object.entries(a).map(([r, y]) => ({ type: r, title: "", items: y }));
      }
    },
    // ═══ 委托代理（3 action）═══
    processSurrogate: {
      page: (a = {}) => n("processSurrogate/page", a),
      save: (a) => n("processSurrogate/save", a),
      remove: (a) => n("processSurrogate/remove", { id: a })
    }
  };
  return { api: c, can: s };
}
const Jt = Symbol("jeeflow-ui");
function sl(e) {
  const l = e.adapters || {}, i = e.listUsers;
  return {
    ...l,
    listUsers: l.listUsers || (i ? (n, s) => i(n) : void 0)
  };
}
function Yt(e) {
  const l = String(e);
  return l === "10" || l === "DOING" ? "进行中" : l === "20" || l === "DONE" || l === "FINISHED" ? "已完成" : l === "30" || l === "WITHDRAW" ? "已撤回" : l === "40" || l === "INTERRUPT" ? "已终止" : l === "45" || l === "REJECT" ? "已拒绝" : l === "50" || l === "PENDING" ? "挂起" : l === "99" || l === "ABANDON" ? "已废弃" : e != null ? String(e) : "-";
}
function $n(e) {
  const l = String(e);
  return l === "10" || l === "DOING" ? "doing" : l === "20" || l === "DONE" || l === "FINISHED" ? "done" : l === "45" || l === "REJECT" || l === "99" ? "reject" : "info";
}
function ol(e) {
  const l = String(e);
  return l === "10" || l === "DOING" ? "待办" : l === "20" || l === "FINISHED" ? "已完成" : l === "99" || l === "ABANDON" ? "已废弃" : l === "30" || l === "WITHDRAW" ? "已撤回" : l === "40" || l === "INTERRUPT" ? "已终止" : e != null ? String(e) : "-";
}
function wn(e) {
  const l = String(e);
  return l === "10" || l === "DOING" ? "doing" : l === "20" || l === "FINISHED" ? "done" : l === "99" || l === "ABANDON" ? "reject" : "info";
}
function xe(e, l = !1) {
  if (!e) return "";
  const i = new Date(e);
  if (isNaN(i.getTime())) return e;
  if (l)
    return i.toLocaleString("zh-CN", { month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" });
  const n = (s) => String(s).padStart(2, "0");
  return `${i.getFullYear()}-${n(i.getMonth() + 1)}-${n(i.getDate())} ${n(i.getHours())}:${n(i.getMinutes())}:${n(i.getSeconds())}`;
}
function mt(e) {
  return e === "snaker:task" || e === "task";
}
function Et(e) {
  const l = (e == null ? void 0 : e.nodes) || [], i = (e == null ? void 0 : e.edges) || [], n = l.find((s) => (s == null ? void 0 : s.type) === "snaker:start" || (s == null ? void 0 : s.type) === "start");
  if (n) {
    const s = i.find((c) => c.sourceNodeId === n.id);
    if (s) {
      const c = l.find((a) => a.id === s.targetNodeId && mt(a == null ? void 0 : a.type));
      if (c) return c;
    }
  }
  return l.find((s) => mt(s == null ? void 0 : s.type)) || null;
}
function il(e, l) {
  return l && ((e == null ? void 0 : e.nodes) || []).find(
    (n) => {
      var s, c;
      return mt(n == null ? void 0 : n.type) && (n.id === l || ((s = n.properties) == null ? void 0 : s.name) === l || ((c = n.text) == null ? void 0 : c.value) === l);
    }
  ) || null;
}
function _n(e) {
  var n, s;
  const l = Et(e);
  if ((n = l == null ? void 0 : l.properties) != null && n.form) return l.properties.form;
  for (const c of (e == null ? void 0 : e.nodes) || [])
    if (mt(c == null ? void 0 : c.type) && ((s = c == null ? void 0 : c.properties) != null && s.form)) return c.properties.form;
  const i = e == null ? void 0 : e.instanceUrl;
  return typeof i == "string" && i && !i.includes("/") ? i : "";
}
function Ic(e) {
  var i, n;
  const l = [];
  for (const s of (e == null ? void 0 : e.nodes) || [])
    mt(s == null ? void 0 : s.type) && l.push({ id: s.id, displayName: ((i = s.text) == null ? void 0 : i.value) || s.id, form: (n = s.properties) == null ? void 0 : n.form });
  return l;
}
const pt = { READ_ONLY: 1, EDIT: 2, HIDDEN: 3 };
function ut(e) {
  return e === 1 || e === !0 || e === "1";
}
function yt(e) {
  var n;
  const l = e == null ? void 0 : e.__schema__;
  if (!l || typeof l != "object") return null;
  const i = (n = l.ext) == null ? void 0 : n.layout;
  return Array.isArray(l.columns) && l.columns.length ? {
    layout: i,
    columns: l.columns.map((s) => ({
      fieldName: String(s.fieldName || s.fieldCamelName || "").replace(/^f_/, ""),
      remark: s.remark || s.label || s.fieldName || "",
      component: s.component || "Input",
      ext: s.ext || {}
    })).filter((s) => s.fieldName)
  } : Array.isArray(l.fields) && l.fields.length ? {
    layout: i,
    columns: l.fields.map((s) => ({
      fieldName: String(s.key || s.fieldName || "").replace(/^f_/, ""),
      remark: s.label || s.remark || s.key || "",
      component: s.component || "Input",
      ext: s.ext || {}
    })).filter((s) => s.fieldName)
  } : null;
}
function Wt(e, l = "f_") {
  const i = yt(e);
  if (!i) return {};
  const n = {};
  for (const s of i.columns)
    n[`${l}${s.fieldName}`] = s.remark || s.fieldName, n[s.fieldName] = s.remark || s.fieldName;
  return n;
}
function rl(e, l, i) {
  var c;
  if (!ut(e == null ? void 0 : e.enableFieldPerm)) return pt.EDIT;
  const n = ((c = l == null ? void 0 : l.properties) == null ? void 0 : c.field) || (l == null ? void 0 : l.ext) || {}, s = String(i).replace(/^f_/, "").replace(/^tf_/, "");
  for (const a of [`PERMISSION_f_${s}`, `PERMISSION_${s}`, `PERMISSION_tf_${s}`]) {
    const r = Number(n[a]);
    if (r === 1 || r === 2 || r === 3) return r;
  }
  return pt.EDIT;
}
function Gt(e, l, i) {
  var c;
  const n = {}, s = i ?? ((c = yt(e)) == null ? void 0 : c.columns) ?? [];
  for (const a of s) {
    const r = rl(e, l, a.fieldName);
    n[a.fieldName] = r, n[`f_${a.fieldName}`] = r;
  }
  return n;
}
function dl(e) {
  return e === 1 || e === "1" || e === "COUNTERSIGN" || e === "ALL";
}
function ul(e, l) {
  var n, s;
  const i = (n = e == null ? void 0 : e.properties) == null ? void 0 : n.actionBtns;
  return Array.isArray(i) && i.length ? i.filter((c) => typeof c == "string") : dl(l ?? ((s = e == null ? void 0 : e.properties) == null ? void 0 : s.performType)) ? ["AGREE", "COUNTERSIGN_DISAGREE", "ADD_CANDIDATE"] : ["AGREE", "REJECT", "ROLLBACK", "ROLLBACK_TO_OPERATOR", "JUMP"];
}
function an(e) {
  return {
    0: "发起申请",
    1: "同意",
    2: "拒绝",
    3: "退回上一步",
    4: "跳转",
    5: "重新提交",
    6: "退回发起人",
    20: "会签拒绝"
  }[String(e)] ?? (e != null ? String(e) : "-");
}
function cl(e) {
  const l = ut(e == null ? void 0 : e.selectUserOnInitiate), i = ut(e == null ? void 0 : e.enableCcActors), n = ut(e == null ? void 0 : e.enableApplyReason), s = ut(e == null ? void 0 : e.enableAttachment);
  return { selectUser: l, cc: i, reason: n, attachment: s, any: l || i || n || s };
}
function Vt(e) {
  if (!e) return {};
  let l = null;
  if (e.formData && typeof e.formData == "object") l = e.formData;
  else if (e.instanceExt && typeof e.instanceExt == "object") l = e.instanceExt;
  else if (e.ext && typeof e.ext == "object") l = e.ext;
  else if (typeof e.instanceVariable == "string")
    try {
      l = JSON.parse(e.instanceVariable);
    } catch {
      l = null;
    }
  else e.variable && typeof e.variable == "object" && (l = e.variable);
  if (!l) return {};
  const i = {};
  for (const [n, s] of Object.entries(l))
    n.startsWith("f_") && (i[n] = s);
  return i;
}
function Ht(e) {
  return e === "SchemaWfForm" || e === "SchemaTfForm";
}
const fl = { class: "jf-schema-form" }, pl = {
  key: 0,
  class: "jf-muted",
  style: { padding: "8px 0" }
}, vl = { class: "jf-form-label" }, ml = {
  key: 0,
  class: "jf-req"
}, hl = ["disabled", "placeholder", "value", "onInput"], yl = ["disabled", "value", "onChange"], gl = { value: "" }, bl = ["value"], kl = ["onChange"], jl = {
  key: 1,
  class: "jf-muted",
  style: { "margin-top": "4px" }
}, $l = ["type", "disabled", "placeholder", "value", "onInput"], wl = {
  key: 4,
  class: "jf-form-error"
}, Xe = /* @__PURE__ */ q({
  name: "JeeflowSchemaForm",
  __name: "JfSchemaForm",
  props: {
    modelValue: { default: () => ({}) },
    schema: { default: null },
    fieldLabels: { default: () => ({}) },
    permissions: { default: () => ({}) },
    readonly: { type: Boolean, default: !1 },
    fieldPrefix: { default: "f_" },
    emptyHint: { default: "未配置表单字段，可直接发起" }
  },
  emits: ["update:modelValue"],
  setup(e, { expose: l, emit: i }) {
    var pe;
    const n = e, s = i, c = Ue({}), a = Ue({}), r = ((pe = Ft(Jt, null)) == null ? void 0 : pe.adapters) || {};
    function y($) {
      return $.startsWith("f_") || $.startsWith("tf_") ? $ : `${n.fieldPrefix}${$}`;
    }
    function v($) {
      const _ = $.fieldName;
      return n.permissions[_] ?? n.permissions[y(_)] ?? pt.EDIT;
    }
    function h($) {
      return n.readonly || v($) === pt.READ_ONLY;
    }
    function p($) {
      var x;
      const _ = (x = $.ext) == null ? void 0 : x.required;
      return _ === 1 || _ === !0 || _ === "1";
    }
    function f($) {
      const _ = ($ || "").toLowerCase();
      return _ === "select" || _ === "radio" || _ === "apidict" || _ === "apiselect";
    }
    function j($) {
      return ($ || "").toLowerCase() === "upload";
    }
    function g($) {
      return ($ || "").toLowerCase() === "textarea";
    }
    function C($) {
      var _, x, L;
      return String(((_ = $.ext) == null ? void 0 : _.dictCode) || ((x = $.ext) == null ? void 0 : x.code) || ((L = $.ext) == null ? void 0 : L.dictType) || "");
    }
    function D($) {
      var x, L;
      if ((L = (x = $.ext) == null ? void 0 : x.options) != null && L.length) return $.ext.options;
      const _ = C($);
      return _ && a[_] || [];
    }
    function T($) {
      const _ = ($ || "Input").toLowerCase();
      return _ === "inputnumber" || _ === "number" ? "number" : _ === "datepicker" || _ === "date" ? "date" : _ === "datetimepicker" || _ === "datetime" ? "datetime-local" : "text";
    }
    function N($) {
      var _;
      return ((_ = $.ext) == null ? void 0 : _.placeholder) || `请输入${$.remark || $.fieldName}`;
    }
    const U = E(() => {
      const $ = n.fieldLabels;
      return Array.from(/* @__PURE__ */ new Set([
        ...Object.keys($),
        ...Object.keys(n.modelValue).filter((x) => {
          const L = n.modelValue[x];
          return L !== "" && L != null && (x.startsWith("f_") || x.startsWith("tf_") || x.startsWith(n.fieldPrefix));
        })
      ])).map((x) => ({
        fieldName: x.replace(/^f_/, "").replace(/^tf_/, ""),
        remark: $[x] ?? $[x.replace(/^f_/, "")] ?? x.replace(/^f_/, "").replace(/^tf_/, ""),
        component: "Input",
        ext: {}
      }));
    }), P = E(() => {
      var $, _;
      return (_ = ($ = n.schema) == null ? void 0 : $.columns) != null && _.length ? n.schema.columns : U.value;
    }), B = E(
      () => P.value.filter(($) => v($) !== pt.HIDDEN)
    );
    function V($) {
      var L;
      const _ = Number((L = $.ext) == null ? void 0 : L.span);
      if (!_ || _ >= 24) return { flex: "1 1 100%" };
      const x = Math.max(25, Math.round(_ / 24 * 100));
      return { flex: `1 1 ${x}%`, maxWidth: `${x}%` };
    }
    function F($) {
      const _ = y($.fieldName);
      return n.modelValue[_] ?? n.modelValue[$.fieldName] ?? "";
    }
    function S($, _) {
      const x = y($.fieldName);
      s("update:modelValue", { ...n.modelValue, [x]: _ }), c[$.fieldName] && delete c[$.fieldName];
    }
    function z($, _) {
      const x = _.target;
      S($, x.type === "number" ? x.value === "" ? "" : Number(x.value) : x.value);
    }
    async function W($, _) {
      var L;
      const x = (L = _.target.files) == null ? void 0 : L[0];
      if (!x) {
        S($, "");
        return;
      }
      if (r.upload)
        try {
          S($, await r.upload(x));
        } catch {
          S($, x.name);
        }
      else
        S($, x.name);
    }
    be(() => n.modelValue, () => {
      for (const $ of Object.keys(c)) delete c[$];
    }), be(P, async ($) => {
      const _ = r.getDict;
      if (_)
        for (const x of $) {
          const L = (x.component || "").toLowerCase();
          if (L !== "apidict" && L !== "apiselect") continue;
          const ie = C(x);
          if (!(!ie || a[ie]))
            try {
              a[ie] = await _(ie) || [];
            } catch {
              a[ie] = [];
            }
        }
    }, { immediate: !0 });
    function fe() {
      for (const $ of Object.keys(c)) delete c[$];
      for (const $ of B.value) {
        if (h($) || !p($)) continue;
        const _ = F($);
        if (_ === "" || _ == null) {
          const x = `请填写${$.remark || $.fieldName}`;
          return c[$.fieldName] = x, x;
        }
      }
      return null;
    }
    return l({ validate: fe }), ($, _) => (o(), u("div", fl, [
      B.value.length ? M("", !0) : (o(), u("div", pl, w(e.emptyHint), 1)),
      (o(!0), u(G, null, le(B.value, (x) => (o(), u("div", {
        key: x.fieldName,
        class: "jf-form-item",
        style: ce(V(x))
      }, [
        t("label", vl, [
          ee(w(x.remark || x.fieldName) + " ", 1),
          p(x) && !h(x) ? (o(), u("span", ml, "*")) : M("", !0)
        ]),
        g(x.component) ? (o(), u("textarea", {
          key: 0,
          class: "jf-input",
          rows: "3",
          disabled: h(x),
          placeholder: N(x),
          value: String(F(x) ?? ""),
          onInput: (L) => S(x, L.target.value)
        }, null, 40, hl)) : f(x.component) ? (o(), u("select", {
          key: 1,
          class: "jf-input",
          disabled: h(x),
          value: String(F(x) ?? ""),
          onChange: (L) => S(x, L.target.value)
        }, [
          t("option", gl, w(N(x)), 1),
          (o(!0), u(G, null, le(D(x), (L) => (o(), u("option", {
            key: String(L.value),
            value: String(L.value)
          }, w(L.label), 9, bl))), 128))
        ], 40, yl)) : j(x.component) ? (o(), u(G, { key: 2 }, [
          h(x) ? M("", !0) : (o(), u("input", {
            key: 0,
            class: "jf-input",
            type: "file",
            onChange: (L) => W(x, L)
          }, null, 40, kl)),
          F(x) ? (o(), u("div", jl, w(String(F(x))), 1)) : M("", !0)
        ], 64)) : (o(), u("input", {
          key: 3,
          class: "jf-input",
          type: T(x.component),
          disabled: h(x),
          placeholder: N(x),
          value: F(x) ?? "",
          onInput: (L) => z(x, L)
        }, null, 40, $l)),
        c[x.fieldName] ? (o(), u("div", wl, w(c[x.fieldName]), 1)) : M("", !0)
      ], 4))), 128))
    ]));
  }
});
function _l() {
  const e = /* @__PURE__ */ new Map();
  function l(n, s, c) {
    if (!n) throw new Error("registerForm: formKey 不能为空");
    e.set(n, { component: s, options: c });
  }
  function i(n, s) {
    var a;
    const c = e.get(n);
    return !c || s && ((a = c.options) != null && a.scenes) && !c.options.scenes.includes(s) ? null : c.component;
  }
  return { register: l, get: i, has: (n) => e.has(n), keys: () => [...e.keys()] };
}
function Cl(e) {
  const { api: l, can: i } = al(e), n = _l();
  return {
    api: l,
    can: i,
    registerForm: n.register.bind(n),
    getForm: n.get.bind(n),
    config: e,
    adapters: sl(e)
  };
}
function je() {
  const e = Ft(Jt);
  if (!e)
    throw new Error("useJeeflowUi 必须在 <JeeflowUiProvider> 内使用（或先调用 createJeeflowUi）");
  return e;
}
const xc = q({
  name: "JeeflowUiProvider",
  props: {
    config: { type: Object, required: !0 }
  },
  setup(e, { slots: l }) {
    const i = Cl(e.config);
    return jn(Jt, i), () => {
      var n;
      return (n = l.default) == null ? void 0 : n.call(l);
    };
  }
}), Il = { class: "jf-drawer__header" }, xl = { class: "jf-drawer__title" }, Dl = /* @__PURE__ */ q({
  name: "JfDrawer",
  __name: "JfDrawer",
  props: {
    visible: { type: Boolean, default: !1 },
    title: { type: String, default: "" },
    width: { type: String, default: "780px" },
    maskClosable: { type: Boolean, default: !0 },
    /** 内容铺满（流程图 Tab / 定义详情）；表单类抽屉保持滚动 */
    fill: { type: Boolean, default: !1 }
  },
  emits: ["update:visible", "close"],
  setup(e, { emit: l }) {
    const i = e, n = l, s = b(!1), c = b(!1), a = b(!1);
    function r() {
      a.value = !1, s.value = !0, document.body.style.overflow = "hidden", requestAnimationFrame(() => {
        requestAnimationFrame(() => {
          c.value = !0;
        });
      });
    }
    function y() {
      !s.value || a.value || (a.value = !0, c.value = !1, setTimeout(() => {
        s.value = !1, a.value = !1, document.body.style.overflow = "", n("update:visible", !1), n("close");
      }, 260));
    }
    function v() {
      y();
    }
    function h() {
      i.maskClosable && y();
    }
    function p(f) {
      s.value && f.key === "Escape" && y();
    }
    return be(() => i.visible, (f) => {
      f ? r() : y();
    }, { immediate: !0 }), he(() => document.addEventListener("keydown", p)), We(() => {
      document.removeEventListener("keydown", p), document.body.style.overflow = "";
    }), (f, j) => (o(), ae(ht, { to: "body" }, [
      s.value ? (o(), u("div", {
        key: 0,
        class: ne(["jf-drawer-root", { "jf-drawer-root--open": c.value }]),
        onClick: Se(h, ["self"])
      }, [
        t("div", {
          class: ne(["jf-drawer", { "jf-drawer--open": c.value }]),
          style: ce({ width: e.width })
        }, [
          t("div", Il, [
            t("span", xl, w(e.title), 1),
            ke(f.$slots, "header-extra"),
            t("button", {
              class: "jf-drawer__close",
              onClick: v
            }, "×")
          ]),
          t("div", {
            class: ne(["jf-drawer__body", { "jf-drawer__body--fill": e.fill }])
          }, [
            ke(f.$slots, "default")
          ], 2)
        ], 6)
      ], 2)) : M("", !0)
    ]));
  }
}), $e = (e, l) => {
  const i = e.__vccOpts || e;
  for (const [n, s] of l)
    i[n] = s;
  return i;
}, Ve = /* @__PURE__ */ $e(Dl, [["__scopeId", "data-v-602d1fbb"]]), Nl = /* @__PURE__ */ q({
  name: "JfBadge",
  __name: "JfBadge",
  props: {
    text: {},
    type: { default: "info" }
  },
  setup(e) {
    return (l, i) => (o(), u("span", {
      class: ne(["jf-badge", `jf-badge--${e.type}`])
    }, [
      ke(l.$slots, "default", {}, () => [
        ee(w(e.text), 1)
      ], !0)
    ], 2));
  }
}), Oe = /* @__PURE__ */ $e(Nl, [["__scopeId", "data-v-8774d34f"]]), Tl = {
  value: {
    type: Object,
    default() {
      return {};
    }
  },
  theme: {
    // 高亮主题配置
    type: Object,
    default() {
      return {};
    }
  },
  highLight: {
    // 高亮数据
    type: Object,
    default() {
      return {};
    }
  },
  initDndPanel: {
    // 是否初始化拖拽面板
    type: Boolean,
    default: !0
  },
  dndPanel: {
    // 拖拽面板
    type: Array
  },
  initControl: {
    // 是否初始化控制面板
    type: Boolean,
    default: !0
  },
  control: {
    // 控制面板
    type: Array
  },
  nodeClick: {
    // 节点点击事件
    type: Function
  },
  edgeClick: {
    // 边点击事件
    type: Function
  },
  blankContextmenu: {
    // 画布右键菜单
    type: Function
  },
  drawerWidth: {
    // 抽屉宽度
    type: [String, Number],
    default: "600px"
  },
  modalWidth: {
    // 弹窗宽度
    type: [String, Number],
    default: "60%"
  },
  processForm: {
    // 流程表单配置
    type: Object
  },
  edgeForm: {
    // 边表单配置
    type: Object
  },
  defaultEdgeType: {
    // 默认边
    type: String,
    default: "snaker:transition"
  },
  typePrefix: {
    // 自定义节点/边类型前缀,如snaker:task,snaker:transition，只是snaker:则为前辍
    type: String,
    default: "snaker:"
  },
  mode: {
    // 渲染模式
    type: String,
    default: void 0
  },
  viewer: {
    // 是否查看模式
    type: Boolean,
    default: !1
  },
  dagreOptions: {
    // dagre配置
    type: Object,
    default: () => ({
      rankdir: "LR",
      align: "UR",
      nodesep: 100,
      ranksep: 80,
      ranker: "network-simplex",
      // 更智能的排名算法
      isDefaultAnchor: !0,
      // 自动优化连线路径
      edgesep: 15
    })
  }
};
function Ce(e) {
  return e.type === "condition";
}
function Ie(e) {
  return e.type === "fork";
}
function Be(e, l) {
  if (!e) return null;
  if (l(e)) return e;
  if (e.branches) {
    const i = e;
    for (const n of i.branches)
      if (n.children) {
        const s = Be(n.children, l);
        if (s) return s;
      }
  }
  if (e.branches) {
    const i = e;
    for (const n of i.branches)
      if (n.children) {
        const s = Be(n.children, l);
        if (s) return s;
      }
    if (i.joinChildren) {
      const n = Be(i.joinChildren, l);
      if (n) return n;
    }
  }
  return "children" in e && e.children ? Be(e.children, l) : null;
}
function ct(e, l = [], i = /* @__PURE__ */ new Set()) {
  if (!e || i.has(e.id)) return l;
  i.add(e.id), l.push(e);
  const n = e;
  if (n.branches)
    for (const c of n.branches)
      c.children && ct(c.children, l, i);
  const s = e;
  if (s.branches) {
    for (const c of s.branches)
      c.children && ct(c.children, l, i);
    s.joinChildren && ct(s.joinChildren, l, i);
  }
  return "children" in e && e.children && ct(e.children, l, i), l;
}
const Cn = "snaker:";
function It(e, l, i = Cn) {
  if (!e.length) return;
  const n = new Map(e.map((a) => [a.id, a])), s = Kt(l), c = e.find((a) => a.type === `${i}start`);
  if (c)
    return nt(c.id, /* @__PURE__ */ new Set(), n, s, l, i);
}
function nt(e, l, i, n, s, c, a = /* @__PURE__ */ new Set()) {
  var r, y;
  if (l.has(e)) return;
  const v = i.get(e);
  if (!v) return;
  if (a.has(e))
    return {
      id: v.id,
      type: v.type,
      name: ((r = v.text) == null ? void 0 : r.value) || "",
      properties: { ...v.properties }
    };
  a.add(e);
  const h = n.get(e) || [], p = v.type.replace(c, "");
  if (p === "decision" && h.length > 1)
    return Pl(v, h, l, i, n, s, c, a);
  if (p === "fork" && h.length > 1)
    return Ml(v, h, l, i, n, s, c, a);
  const f = {
    id: v.id,
    type: v.type,
    name: ((y = v.text) == null ? void 0 : y.value) || "",
    properties: { ...v.properties }
  };
  if (p === "end") return f;
  if (h.length === 1) {
    const j = nt(h[0].targetNodeId, l, i, n, s, c, a);
    j && (f.children = j);
  }
  return f;
}
function Pl(e, l, i, n, s, c, a, r) {
  var y;
  const v = Ll(
    l.map((j) => j.targetNodeId),
    c,
    e.id,
    n,
    a
  ), h = new Set(i);
  v && h.add(v);
  const p = l.map((j) => {
    var g;
    const C = nt(
      j.targetNodeId,
      h,
      n,
      s,
      c,
      a,
      r
    );
    return {
      id: j.id,
      name: ((g = j.text) == null ? void 0 : g.value) || "",
      properties: { ...j.properties },
      children: C
    };
  }), f = {
    id: e.id,
    type: "condition",
    name: ((y = e.text) == null ? void 0 : y.value) || "",
    properties: { ...e.properties },
    branches: p
  };
  if (v) {
    const j = nt(v, i, n, s, c, a, r);
    j && (f.children = j);
  }
  return f;
}
function Ml(e, l, i, n, s, c, a, r) {
  var y;
  const v = El(
    l.map((j) => j.targetNodeId),
    c,
    n,
    a
  ), h = new Set(i);
  v && h.add(v);
  const p = l.map((j) => {
    var g;
    const C = nt(
      j.targetNodeId,
      h,
      n,
      s,
      c,
      a,
      r
    );
    return {
      id: j.id,
      name: ((g = j.text) == null ? void 0 : g.value) || "",
      properties: { ...j.properties },
      children: C
    };
  }), f = {
    id: e.id,
    type: "fork",
    name: ((y = e.text) == null ? void 0 : y.value) || "",
    properties: { ...e.properties },
    branches: p
  };
  if (v) {
    f.joinId = v;
    const j = nt(
      v,
      i,
      n,
      s,
      c,
      a,
      r
    );
    j && (f.joinChildren = j);
  }
  return f;
}
function El(e, l, i, n) {
  const s = Kt(l), c = /* @__PURE__ */ new Set(), a = [...e];
  for (; a.length > 0; ) {
    const r = a.shift();
    if (c.has(r)) continue;
    c.add(r);
    const y = i.get(r);
    if (y && y.type === `${n}join`) return r;
    const v = s.get(r) || [];
    for (const h of v)
      c.has(h.targetNodeId) || a.push(h.targetNodeId);
  }
  return null;
}
function Ll(e, l, i, n, s) {
  const c = Kt(l), a = e.length, r = /* @__PURE__ */ new Map();
  for (const h of e) {
    const p = /* @__PURE__ */ new Set(), f = [h];
    for (; f.length > 0; ) {
      const j = f.shift();
      if (p.has(j)) continue;
      p.add(j), r.set(j, (r.get(j) || 0) + 1);
      const g = c.get(j) || [];
      for (const C of g)
        p.has(C.targetNodeId) || f.push(C.targetNodeId);
    }
  }
  const y = /* @__PURE__ */ new Set([i]), v = [...e];
  for (; v.length > 0; ) {
    const h = v.shift();
    if (y.has(h)) continue;
    if (y.add(h), r.get(h) === a)
      return h;
    const p = c.get(h) || [];
    for (const f of p)
      y.has(f.targetNodeId) || v.push(f.targetNodeId);
  }
  if (n && s) {
    for (const [h, p] of n)
      if (p.type === `${s}end`) return h;
  }
  return null;
}
function xt(e, l = Cn) {
  if (!e) return { nodes: [], edges: [] };
  const i = {
    nodes: [],
    edges: [],
    edgeCounter: 0,
    prefix: l,
    layoutY: 200,
    layoutX: 480
  };
  return lt(e, i), { nodes: i.nodes, edges: i.edges };
}
function lt(e, l) {
  if (Ce(e))
    return Al(e, l);
  if (Ie(e))
    return Sl(e, l);
  const i = Qt(e, l);
  if (l.nodes.push(i), e.children) {
    const n = lt(e.children, l);
    qe(l, e.id, n);
  }
  return e.id;
}
function Al(e, l) {
  const i = Qt(
    { ...e, type: `${l.prefix}decision` },
    l
  );
  l.nodes.push(i);
  const n = l.layoutY, s = e.branches.length, c = l.layoutX - (s - 1) * 200 / 2;
  for (let a = 0; a < s; a++) {
    const r = e.branches[a], y = c + a * 200;
    if (r.children) {
      l.layoutX = y, l.layoutY = n + 150;
      const v = lt(r.children, l);
      if (qe(l, e.id, v, r.id, r.name, r.properties), e.children) {
        const h = vt(r.children);
        qe(l, h, e.children.id);
      }
    } else e.children && qe(l, e.id, e.children.id, r.id, r.name, r.properties);
  }
  return l.layoutX = i.x, l.layoutY = n + 150 * 2, e.children && lt(e.children, l), e.id;
}
function Sl(e, l) {
  const i = Qt(
    { ...e, type: `${l.prefix}fork` },
    l
  );
  l.nodes.push(i);
  const n = l.layoutY, s = e.branches.length, c = l.layoutX - (s - 1) * 200 / 2, a = e.joinId || (e.joinChildren ? e.joinChildren.id : null) || `${e.id}__join`;
  for (let r = 0; r < s; r++) {
    const y = e.branches[r], v = c + r * 200;
    if (!y.children) {
      qe(l, e.id, a);
      continue;
    }
    l.layoutX = v, l.layoutY = n + 150;
    const h = lt(y.children, l);
    qe(l, e.id, h);
    const p = vt(y.children);
    qe(l, p, a);
  }
  return e.joinChildren && (l.layoutX = i.x, l.layoutY = n + 150 * 2, lt(e.joinChildren, l)), e.id;
}
function Kt(e) {
  const l = /* @__PURE__ */ new Map();
  for (const i of e) {
    const n = l.get(i.sourceNodeId);
    n ? n.push(i) : l.set(i.sourceNodeId, [i]);
  }
  return l;
}
function Qt(e, l) {
  const i = l.layoutX, n = l.layoutY;
  return l.layoutY += 150, {
    id: e.id,
    type: e.type,
    x: i,
    y: n,
    text: e.name ? { x: i, y: n, value: e.name } : void 0,
    properties: { ...e.properties }
  };
}
function qe(e, l, i, n, s, c) {
  const r = {
    id: n || `edge_${++e.edgeCounter}`,
    type: `${e.prefix}transition`,
    sourceNodeId: l,
    targetNodeId: i,
    properties: c ? { ...c } : {}
  };
  s && (r.text = { value: s }), e.edges.push(r);
}
function vt(e) {
  return Ce(e) ? e.children ? vt(e.children) : e.id : Ie(e) ? e.joinChildren ? vt(e.joinChildren) : e.id : e.children ? vt(e.children) : e.id;
}
const Ol = [
  {
    id: "start",
    type: "snaker:start",
    x: 280,
    y: 280,
    properties: { width: 120, height: 80 },
    text: { x: 280, y: 320, value: "开始" }
  },
  {
    id: "apply",
    type: "snaker:task",
    x: 480,
    y: 280,
    properties: {
      width: 120,
      height: 80,
      // 发起申请节点：assignee = "applicant"（引擎解析为发起人）
      assignee: "applicant",
      taskType: "Major",
      performType: "ANY",
      autoExecute: "N"
    },
    text: { x: 480, y: 280, value: "发起申请" }
  },
  {
    id: "end",
    type: "snaker:end",
    x: 680,
    y: 280,
    properties: { width: 120, height: 80 },
    text: { x: 680, y: 320, value: "结束" }
  }
], zl = [
  {
    id: "t1",
    type: "snaker:transition",
    sourceNodeId: "start",
    targetNodeId: "apply",
    properties: {}
  },
  {
    id: "t2",
    type: "snaker:transition",
    sourceNodeId: "apply",
    targetNodeId: "end",
    properties: {}
  }
], Me = (e, l) => {
  const i = e.__vccOpts || e;
  for (const [n, s] of l)
    i[n] = s;
  return i;
}, Bl = ["type", "value", "placeholder", "disabled", "readonly"], Ul = /* @__PURE__ */ q({
  __name: "FDInput",
  props: {
    modelValue: { default: "" },
    type: { default: "text" },
    placeholder: { default: "" },
    disabled: { type: Boolean, default: !1 },
    readonly: { type: Boolean, default: !1 }
  },
  emits: ["update:modelValue"],
  setup(e, { emit: l }) {
    const i = l;
    function n(s) {
      i("update:modelValue", s.target.value);
    }
    return (s, c) => (o(), u("input", {
      class: ne(["fd-input", { "fd-input--disabled": e.disabled }]),
      type: e.type,
      value: e.modelValue,
      placeholder: e.placeholder,
      disabled: e.disabled,
      readonly: e.readonly,
      onInput: n
    }, null, 42, Bl));
  }
}), Vl = /* @__PURE__ */ Me(Ul, [["__scopeId", "data-v-418f77f7"]]), Rl = ["value", "placeholder", "disabled", "readonly", "rows"], Fl = /* @__PURE__ */ q({
  __name: "FDTextarea",
  props: {
    modelValue: { default: "" },
    placeholder: { default: "" },
    rows: { default: 4 },
    disabled: { type: Boolean, default: !1 },
    readonly: { type: Boolean, default: !1 }
  },
  emits: ["update:modelValue"],
  setup(e, { emit: l }) {
    const i = l;
    function n(s) {
      i("update:modelValue", s.target.value);
    }
    return (s, c) => (o(), u("textarea", {
      class: ne(["fd-textarea", { "fd-textarea--disabled": e.disabled }]),
      value: e.modelValue,
      placeholder: e.placeholder,
      disabled: e.disabled,
      readonly: e.readonly,
      rows: e.rows,
      onInput: n
    }, null, 42, Rl));
  }
}), Jl = /* @__PURE__ */ Me(Fl, [["__scopeId", "data-v-86b32aee"]]), Yl = {
  key: 0,
  class: "fd-select__value"
}, Wl = {
  key: 1,
  class: "fd-select__placeholder"
}, Gl = {
  key: 0,
  class: "fd-select__empty"
}, Hl = ["onClick"], Kl = /* @__PURE__ */ q({
  __name: "FDSelect",
  props: {
    modelValue: {},
    options: { default: () => [] },
    placeholder: { default: "请选择" },
    disabled: { type: Boolean, default: !1 }
  },
  emits: ["update:modelValue", "change"],
  setup(e, { emit: l }) {
    const i = e, n = l, s = b(!1), c = b(null), a = b({ x: 0, y: 0, w: 0 }), r = E(() => {
      const j = i.options.find((g) => g.value === i.modelValue);
      return j == null ? void 0 : j.label;
    }), y = E(() => ({
      left: `${a.value.x}px`,
      top: `${a.value.y}px`,
      minWidth: `${a.value.w}px`
    }));
    function v() {
      if (!c.value) return;
      const j = c.value.getBoundingClientRect();
      a.value = { x: j.left, y: j.bottom + 4, w: j.width };
    }
    function h() {
      i.disabled || (s.value ? s.value = !1 : (v(), s.value = !0, tt(() => {
        document.addEventListener("mousedown", f);
      })));
    }
    function p(j) {
      n("update:modelValue", j.value), n("change", j.value), s.value = !1, document.removeEventListener("mousedown", f);
    }
    function f(j) {
      const g = j.target;
      c.value && c.value.contains(g) || (s.value = !1, document.removeEventListener("mousedown", f));
    }
    return he(() => {
      window.addEventListener("resize", v);
    }), We(() => {
      document.removeEventListener("mousedown", f), window.removeEventListener("resize", v);
    }), (j, g) => (o(), u("div", {
      class: ne(["fd-select", { "fd-select--open": s.value, "fd-select--disabled": e.disabled }]),
      ref_key: "triggerRef",
      ref: c
    }, [
      t("div", {
        class: "fd-select__trigger",
        onClick: h
      }, [
        r.value !== null && r.value !== void 0 && r.value !== "" ? (o(), u("span", Yl, w(r.value), 1)) : (o(), u("span", Wl, w(e.placeholder), 1)),
        t("span", {
          class: ne(["fd-select__arrow", { "fd-select__arrow--up": s.value }])
        }, [...g[0] || (g[0] = [
          t("svg", {
            width: "12",
            height: "12",
            viewBox: "0 0 12 12"
          }, [
            t("path", {
              d: "M2.5 4.5L6 8l3.5-3.5",
              fill: "none",
              stroke: "currentColor",
              "stroke-width": "1.2",
              "stroke-linecap": "round",
              "stroke-linejoin": "round"
            })
          ], -1)
        ])], 2)
      ]),
      (o(), ae(ht, { to: "body" }, [
        J(Nt, { name: "fd-select-drop" }, {
          default: te(() => {
            var C;
            return [
              s.value ? (o(), u("div", {
                key: 0,
                class: "fd-select__dropdown",
                style: ce(y.value)
              }, [
                (C = e.options) != null && C.length ? M("", !0) : (o(), u("div", Gl, "暂无选项")),
                (o(!0), u(G, null, le(e.options, (D) => (o(), u("div", {
                  key: String(D.value),
                  class: ne(["fd-select__option", { "fd-select__option--active": D.value === e.modelValue }]),
                  onClick: (T) => p(D)
                }, w(D.label), 11, Hl))), 128))
              ], 4)) : M("", !0)
            ];
          }),
          _: 1
        })
      ]))
    ], 2));
  }
}), Ql = /* @__PURE__ */ Me(Kl, [["__scopeId", "data-v-6e8ff4e6"]]), Xl = { class: "fd-tooltip__inner" }, ql = /* @__PURE__ */ q({
  __name: "FDTooltip",
  props: {
    title: { default: "" },
    placement: { default: "top" },
    offset: { default: 8 }
  },
  setup(e) {
    const l = e, i = b(!1), n = b(null), s = b(null), c = b({ x: 0, y: 0 });
    function a(v) {
      i.value = !0, tt(() => {
        if (!s.value || !n.value) return;
        const h = n.value.getBoundingClientRect(), p = s.value.getBoundingClientRect(), f = window.innerWidth, j = window.innerHeight;
        let g, C;
        switch (l.placement) {
          case "top":
            g = h.left + h.width / 2 - p.width / 2, C = h.top - p.height - l.offset;
            break;
          case "bottom":
            g = h.left + h.width / 2 - p.width / 2, C = h.bottom + l.offset;
            break;
          case "left":
            g = h.left - p.width - l.offset, C = h.top + h.height / 2 - p.height / 2;
            break;
          case "right":
            g = h.right + l.offset, C = h.top + h.height / 2 - p.height / 2;
            break;
        }
        g = Math.max(4, Math.min(g, f - p.width - 4)), C = Math.max(4, Math.min(C, j - p.height - 4)), c.value = { x: g, y: C };
      });
    }
    function r() {
      i.value = !1;
    }
    const y = E(() => ({
      left: `${c.value.x}px`,
      top: `${c.value.y}px`
    }));
    return (v, h) => (o(), u("div", {
      class: "fd-tooltip",
      ref_key: "triggerRef",
      ref: n,
      onMouseenter: a,
      onMouseleave: r,
      onFocusin: a,
      onFocusout: r
    }, [
      ke(v.$slots, "default", {}, void 0, !0),
      (o(), ae(ht, { to: "body" }, [
        J(Nt, { name: "fd-tooltip-fade" }, {
          default: te(() => [
            i.value ? (o(), u("div", {
              key: 0,
              class: "fd-tooltip__popup",
              style: ce(y.value),
              ref_key: "popupRef",
              ref: s
            }, [
              t("div", Xl, [
                ke(v.$slots, "content", {}, () => [
                  ee(w(e.title), 1)
                ], !0)
              ])
            ], 4)) : M("", !0)
          ]),
          _: 3
        })
      ]))
    ], 544));
  }
}), In = /* @__PURE__ */ Me(ql, [["__scopeId", "data-v-3b6c0f5a"]]), Zl = { class: "fd-drawer__header" }, ea = { class: "fd-drawer__title" }, ta = { class: "fd-drawer__body" }, na = {
  key: 0,
  class: "fd-drawer__footer"
}, la = ["disabled"], aa = /* @__PURE__ */ q({
  __name: "FDDrawer",
  props: {
    visible: { type: Boolean },
    title: { default: "" },
    width: { default: "420px" },
    cancelText: { default: "取消" },
    okText: { default: "确定" },
    okDisabled: { type: Boolean, default: !1 },
    showFooter: { type: Boolean, default: !0 },
    maskClosable: { type: Boolean, default: !0 },
    keyboard: { type: Boolean, default: !0 }
  },
  emits: ["update:visible", "ok", "cancel", "close"],
  setup(e, { emit: l }) {
    const i = e, n = l, s = b(!1), c = b(!1), a = b(!1);
    let r = null;
    const y = b(null);
    function v() {
      if (a.value = !1, r && (clearTimeout(r), r = null), s.value) {
        c.value = !0;
        return;
      }
      s.value = !0, document.body.style.overflow = "hidden", requestAnimationFrame(() => {
        requestAnimationFrame(() => {
          c.value = !0;
        });
      });
    }
    function h() {
      !s.value || a.value || (a.value = !0, c.value = !1, r = setTimeout(() => {
        r = null, s.value = !1, a.value = !1, document.body.style.overflow = "", n("close");
      }, 260));
    }
    function p() {
      h(), n("update:visible", !1), n("cancel");
    }
    function f() {
      n("ok");
    }
    function j() {
      i.maskClosable && p();
    }
    function g(C) {
      !s.value || !i.keyboard || C.key === "Escape" && p();
    }
    return be(() => i.visible, (C) => {
      C ? v() : h();
    }, { immediate: !0 }), he(() => {
      document.addEventListener("keydown", g);
    }), We(() => {
      r && clearTimeout(r), document.removeEventListener("keydown", g), document.body.style.overflow = "";
    }), (C, D) => (o(), ae(ht, { to: "body" }, [
      s.value ? (o(), u("div", {
        key: 0,
        class: ne(["fd-drawer-root", { "fd-drawer-root--open": c.value }]),
        onClick: Se(j, ["self"])
      }, [
        t("div", {
          class: ne(["fd-drawer", { "fd-drawer--open": c.value }]),
          style: ce({ width: e.width }),
          ref_key: "drawerRef",
          ref: y
        }, [
          t("div", Zl, [
            t("span", ea, w(e.title), 1),
            t("button", {
              class: "fd-drawer__close",
              onClick: p
            }, "×")
          ]),
          t("div", ta, [
            ke(C.$slots, "default", {}, void 0, !0)
          ]),
          C.$slots.footer || e.showFooter ? (o(), u("div", na, [
            ke(C.$slots, "footer", {}, () => [
              t("button", {
                class: "fd-btn fd-btn--default",
                onClick: p
              }, w(e.cancelText), 1),
              t("button", {
                class: "fd-btn fd-btn--primary",
                onClick: f,
                disabled: e.okDisabled
              }, w(e.okText), 9, la)
            ], !0)
          ])) : M("", !0)
        ], 6)
      ], 2)) : M("", !0)
    ]));
  }
}), sn = /* @__PURE__ */ Me(aa, [["__scopeId", "data-v-a5ad9d4e"]]), sa = { class: "fd-modal__header" }, oa = { class: "fd-modal__title" }, ia = { class: "fd-modal__body" }, ra = {
  key: 0,
  class: "fd-modal__footer"
}, da = ["disabled"], ua = /* @__PURE__ */ q({
  __name: "FDModal",
  props: {
    visible: { type: Boolean },
    title: { default: "" },
    width: { default: "520px" },
    cancelText: { default: "取消" },
    okText: { default: "确定" },
    okDisabled: { type: Boolean, default: !1 },
    showFooter: { type: Boolean, default: !0 },
    maskClosable: { type: Boolean, default: !0 },
    keyboard: { type: Boolean, default: !0 }
  },
  emits: ["update:visible", "ok", "cancel", "close"],
  setup(e, { emit: l }) {
    const i = e, n = l, s = b(null);
    function c() {
      n("ok");
    }
    function a() {
      n("update:visible", !1), n("cancel");
    }
    function r() {
      i.maskClosable && a();
    }
    function y(v) {
      !i.visible || !i.keyboard || v.key === "Escape" && a();
    }
    return he(() => {
      document.addEventListener("keydown", y);
    }), We(() => {
      document.removeEventListener("keydown", y);
    }), be(() => i.visible, (v) => {
      document.body.style.overflow = v ? "hidden" : "";
    }), (v, h) => (o(), ae(ht, { to: "body" }, [
      J(Nt, { name: "fd-modal-fade" }, {
        default: te(() => [
          e.visible ? (o(), u("div", {
            key: 0,
            class: "fd-modal-root",
            onClick: Se(r, ["self"])
          }, [
            J(Nt, { name: "fd-modal-zoom" }, {
              default: te(() => [
                e.visible ? (o(), u("div", {
                  key: 0,
                  class: "fd-modal",
                  style: ce({ width: e.width }),
                  ref_key: "modalRef",
                  ref: s
                }, [
                  t("div", sa, [
                    t("span", oa, w(e.title), 1),
                    t("button", {
                      class: "fd-modal__close",
                      onClick: a
                    }, "×")
                  ]),
                  t("div", ia, [
                    ke(v.$slots, "default", {}, void 0, !0)
                  ]),
                  v.$slots.footer || e.showFooter ? (o(), u("div", ra, [
                    ke(v.$slots, "footer", {}, () => [
                      t("button", {
                        class: "fd-btn fd-btn--default",
                        onClick: a
                      }, w(e.cancelText), 1),
                      t("button", {
                        class: "fd-btn fd-btn--primary",
                        onClick: c,
                        disabled: e.okDisabled
                      }, w(e.okText), 9, da)
                    ], !0)
                  ])) : M("", !0)
                ], 4)) : M("", !0)
              ]),
              _: 3
            })
          ])) : M("", !0)
        ]),
        _: 3
      })
    ]));
  }
}), on = /* @__PURE__ */ Me(ua, [["__scopeId", "data-v-3e1c6639"]]), ca = { class: "fd-form" }, fa = /* @__PURE__ */ q({
  __name: "FDForm",
  props: {
    labelWidth: { default: "100px" }
  },
  setup(e) {
    const l = e;
    return jn("fdFormLabelWidth", E(() => l.labelWidth)), (i, n) => (o(), u("div", ca, [
      ke(i.$slots, "default", {}, void 0, !0)
    ]));
  }
}), pa = /* @__PURE__ */ Me(fa, [["__scopeId", "data-v-a98e93ea"]]), va = { class: "fd-form-item" }, ma = { class: "fd-form-item__content" }, ha = /* @__PURE__ */ q({
  __name: "FDFormItem",
  props: {
    label: {}
  },
  setup(e) {
    const l = Ft("fdFormLabelWidth", E(() => "120px")), i = E(() => l.value);
    return (n, s) => (o(), u("div", va, [
      e.label || n.$slots.label ? (o(), u("div", {
        key: 0,
        class: "fd-form-item__label",
        style: ce({ width: i.value })
      }, [
        ke(n.$slots, "label", {}, () => [
          ee(w(e.label), 1)
        ], !0)
      ], 4)) : M("", !0),
      t("div", ma, [
        ke(n.$slots, "default", {}, void 0, !0)
      ])
    ]));
  }
}), ya = /* @__PURE__ */ Me(ha, [["__scopeId", "data-v-f03a8db5"]]), ga = "data:image/svg+xml;base64,PHN2ZyB0PSIxNzMzMzE2NTM1ODkwIiBjbGFzcz0iaWNvbiIgdmlld0JveD0iMCAwIDEwMjQgMTAyNCIgdmVyc2lvbj0iMS4xIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHAtaWQ9IjQyOTMiIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCI+PHBhdGggZD0iTTUxMS4wMjM3NTg2NiA4NzMuMjA5Mjk3OTVjLTkyLjc0MjkyNzg1IDAtMTg1LjcyOTkxNjA1LTM1LjM4ODc0ODc3LTI1Ni4yNjMzNTMyOS0xMDUuOTIyMTg2LTE0MS4zMTA5MzQ4MS0xNDEuMzEwOTM0ODEtMTQxLjMxMDkzNDgxLTM3MS4yMTU3NzE3NSAwLTUxMi41MjY3MDY1OCAxNDEuMzEwOTM0ODEtMTQxLjMxMDkzNDgxIDM3MS4yMTU3NzE3NS0xNDEuMzEwOTM0ODEgNTEyLjUyNjcwNjU4IDAgMTQxLjMxMDkzNDgxIDE0MS4zMTA5MzQ4MSAxNDEuMzEwOTM0ODEgMzcxLjIxNTc3MTc1IDAgNTEyLjUyNjcwNjU4LTcwLjc3NzQ5NzU4IDcwLjUzMzQzNzIzLTE2My41MjA0MjU0MyAxMDUuOTIyMTg2MDMtMjU2LjI2MzM1MzI5IDEwNS45MjIxODZ6IG0wLTY2My42MDAwNTQ4MWMtNzcuMTIzMDY2MzEgMC0xNTQuNDkwMTkyOTkgMjkuMjg3MjQwMzYtMjEzLjA2NDY3MzcxIDg4LjEwNTc4MTQ1LTExNy42MzcwODIxNyAxMTcuNjM3MDgyMTctMTE3LjYzNzA4MjE3IDMwOC43MzYzMjU2MiAwIDQyNi4zNzM0MDc4QzM1Ni43Nzc2MjU5OCA3ODIuOTA2OTczNDggNDMzLjkwMDY5MjMyIDgxMi4xOTQyMTM4NSA1MTEuMDIzNzU4NjYgODEyLjE5NDIxMzg1Yzc3LjEyMzA2NjMxIDAgMTU0LjI0NjEzMjY0LTI5LjI4NzI0MDM2IDIxMy4wNjQ2NzM3My04OC4xMDU3ODE0NiAxMTcuNjM3MDgyMTctMTE3LjYzNzA4MjE3IDExNy42MzcwODIxNy0zMDguNzM2MzI1NjIgMC00MjYuMzczNDA3OC01OC44MTg1NDExLTU4LjgxODU0MTEtMTM1Ljk0MTYwNzQxLTg4LjEwNTc4MTQ1LTIxMy4wNjQ2NzM3My04OC4xMDU3ODE0NXoiIGZpbGw9IiM4YThhOGEiIHAtaWQ9IjQyOTQiPjwvcGF0aD48cGF0aCBkPSJNNDc3LjgzMTU1MjkgMzExLjg3MDUyNDExaDYxLjAxNTA4NDF2MjY4LjQ2NjM3MDA5aC02MS4wMTUwODQxek00NzcuODMxNTUyOSA2MzguOTExMzc0OTVoNjEuMDE1MDg0MXY1Ni4xMzM4Nzc0MWgtNjEuMDE1MDg0MXoiIGZpbGw9IiM4YThhOGEiIHAtaWQ9IjQyOTUiPjwvcGF0aD48L3N2Zz4=", ba = ["src"], rn = /* @__PURE__ */ q({
  __name: "FDSchemaForm",
  props: {
    formItems: {},
    model: {},
    labelWidth: { default: "120px" },
    renderContext: {}
  },
  setup(e) {
    return (l, i) => {
      var n;
      return (n = e.formItems) != null && n.length ? (o(), ae(pa, {
        key: 0,
        "label-width": e.labelWidth
      }, {
        default: te(() => [
          (o(!0), u(G, null, le(e.formItems, (s) => (o(), ae(ya, {
            key: s.name,
            label: s.helpMessage && s.helpMessage.length ? void 0 : s.label
          }, el({
            default: te(() => [
              s.component == "Input" ? (o(), ae(Vl, ft({
                key: 0,
                modelValue: e.model[s.name],
                "onUpdate:modelValue": (c) => e.model[s.name] = c
              }, { ref_for: !0 }, { ...s.componentProps }), null, 16, ["modelValue", "onUpdate:modelValue"])) : s.component == "Select" ? (o(), ae(Ql, ft({
                key: 1,
                modelValue: e.model[s.name],
                "onUpdate:modelValue": (c) => e.model[s.name] = c
              }, { ref_for: !0 }, { ...s.componentProps }), null, 16, ["modelValue", "onUpdate:modelValue"])) : s.slot ? ke(l.$slots, s.slot, ft({ ref_for: !0 }, e.renderContext), void 0, void 0, 2) : (o(), ae(Mt(s.render ? s.render(e.renderContext) : void 0), {
                key: 3,
                modelValue: e.model[s.name],
                "onUpdate:modelValue": (c) => e.model[s.name] = c,
                value: e.model[s.name],
                "onUpdate:value": (c) => e.model[s.name] = c,
                checked: e.model[s.name],
                "onUpdate:checked": (c) => e.model[s.name] = c
              }, null, 40, ["modelValue", "onUpdate:modelValue", "value", "onUpdate:value", "checked", "onUpdate:checked"]))
            ]),
            _: 2
          }, [
            s.helpMessage && s.helpMessage.length ? {
              name: "label",
              fn: te(() => [
                ee(w(s.label) + " ", 1),
                J(In, null, {
                  content: te(() => [
                    Array.isArray(s.helpMessage) ? (o(!0), u(G, { key: 0 }, le(s.helpMessage, (c, a) => (o(), u("div", { key: a }, w(c), 1))), 128)) : (o(), u(G, { key: 1 }, [
                      ee(w(s.helpMessage), 1)
                    ], 64))
                  ]),
                  default: te(() => [
                    t("img", { src: H(ga) }, null, 8, ba)
                  ]),
                  _: 2
                }, 1024)
              ]),
              key: "0"
            } : void 0
          ]), 1032, ["label"]))), 128))
        ]),
        _: 3
      }, 8, ["label-width"])) : M("", !0);
    };
  }
}), ka = { class: "fd-json-node" }, ja = { class: "fd-json-key" }, $a = { class: "fd-json-bracket" }, wa = { class: "fd-json-ellipsis" }, _a = { class: "fd-json-bracket" }, Ca = {
  key: 0,
  class: "fd-json-comma"
}, Ia = { class: "fd-json-bracket" }, xa = {
  key: 0,
  class: "fd-json-comma"
}, Da = { class: "fd-json-key" }, Na = {
  key: 1,
  class: "fd-json-comma"
}, Ta = /* @__PURE__ */ q({
  __name: "FDJsonNode",
  props: {
    name: { default: null },
    data: {},
    depth: { default: 0 },
    isLast: { type: Boolean, default: !0 },
    defaultExpandDepth: { default: 2 }
  },
  setup(e) {
    const l = e, i = b(l.depth < l.defaultExpandDepth), n = E(
      () => l.data !== null && typeof l.data == "object"
    ), s = E(() => Array.isArray(l.data)), c = E(() => s.value ? "[" : "{"), a = E(() => s.value ? "]" : "}"), r = E(() => s.value ? l.data.map((j) => ({ name: null, value: j })) : Object.keys(l.data || {}).map((j) => ({ name: j, value: l.data[j] }))), y = E(() => r.value.length), v = E(() => `${l.depth * 16}px`), h = E(() => l.data === null ? "null" : Array.isArray(l.data) ? "object" : typeof l.data), p = E(() => {
      switch (h.value) {
        case "string":
          return `"${l.data}"`;
        case "null":
          return "null";
        default:
          return String(l.data);
      }
    }), f = E(() => `fd-json-value fd-json-value--${h.value}`);
    return (j, g) => (o(), u("div", ka, [
      n.value ? (o(), u(G, { key: 0 }, [
        t("div", {
          class: "fd-json-line",
          style: ce({ paddingLeft: v.value })
        }, [
          t("span", {
            class: "fd-json-toggle",
            onClick: g[0] || (g[0] = (C) => i.value = !i.value)
          }, w(i.value ? "▾" : "▸"), 1),
          e.name !== null ? (o(), u(G, { key: 0 }, [
            t("span", ja, '"' + w(e.name) + '"', 1),
            g[1] || (g[1] = t("span", { class: "fd-json-colon" }, ": ", -1))
          ], 64)) : M("", !0),
          t("span", $a, w(c.value), 1),
          i.value ? M("", !0) : (o(), u(G, { key: 1 }, [
            t("span", wa, "… " + w(y.value) + " 项 ", 1),
            t("span", _a, w(a.value), 1),
            e.isLast ? M("", !0) : (o(), u("span", Ca, ","))
          ], 64))
        ], 4),
        i.value ? (o(), u(G, { key: 0 }, [
          (o(!0), u(G, null, le(r.value, (C, D) => (o(), ae(xn, {
            key: D,
            name: C.name,
            data: C.value,
            depth: e.depth + 1,
            "is-last": D === r.value.length - 1,
            "default-expand-depth": e.defaultExpandDepth
          }, null, 8, ["name", "data", "depth", "is-last", "default-expand-depth"]))), 128)),
          t("div", {
            class: "fd-json-line",
            style: ce({ paddingLeft: v.value })
          }, [
            g[2] || (g[2] = t("span", { class: "fd-json-toggle-placeholder" }, null, -1)),
            t("span", Ia, w(a.value), 1),
            e.isLast ? M("", !0) : (o(), u("span", xa, ","))
          ], 4)
        ], 64)) : M("", !0)
      ], 64)) : (o(), u("div", {
        key: 1,
        class: "fd-json-line",
        style: ce({ paddingLeft: v.value })
      }, [
        g[4] || (g[4] = t("span", { class: "fd-json-toggle-placeholder" }, null, -1)),
        e.name !== null ? (o(), u(G, { key: 0 }, [
          t("span", Da, '"' + w(e.name) + '"', 1),
          g[3] || (g[3] = t("span", { class: "fd-json-colon" }, ": ", -1))
        ], 64)) : M("", !0),
        t("span", {
          class: ne(f.value)
        }, w(p.value), 3),
        e.isLast ? M("", !0) : (o(), u("span", Na, ","))
      ], 4))
    ]));
  }
}), xn = /* @__PURE__ */ Me(Ta, [["__scopeId", "data-v-3306d522"]]), Pa = /* @__PURE__ */ q({
  __name: "FDJsonViewer",
  props: {
    data: {},
    showLineNumber: { type: Boolean, default: !1 },
    defaultExpandDepth: { default: 2 }
  },
  setup(e) {
    return (l, i) => (o(), u("div", {
      class: ne(["fd-json-viewer", { "fd-json-viewer--linenum": e.showLineNumber }])
    }, [
      J(xn, {
        data: e.data,
        depth: 0,
        "is-last": !0,
        "default-expand-depth": e.defaultExpandDepth
      }, null, 8, ["data", "default-expand-depth"])
    ], 2));
  }
}), Ma = /* @__PURE__ */ Me(Pa, [["__scopeId", "data-v-7a0897ee"]]), dn = "fd-message-container", Ea = 3e3, La = {
  success: '<svg width="14" height="14" viewBox="0 0 14 14"><circle cx="7" cy="7" r="6.5" fill="none" stroke="currentColor"/><path d="M4.2 7.2l1.9 1.9 3.7-4" fill="none" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
  error: '<svg width="14" height="14" viewBox="0 0 14 14"><circle cx="7" cy="7" r="6.5" fill="none" stroke="currentColor"/><path d="M5 5l4 4M9 5l-4 4" fill="none" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/></svg>',
  info: '<svg width="14" height="14" viewBox="0 0 14 14"><circle cx="7" cy="7" r="6.5" fill="none" stroke="currentColor"/><path d="M7 6.5v3.5M7 4.2v.1" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/></svg>'
}, Aa = {
  success: "#52c41a",
  error: "#ff4d4f",
  info: "#1677ff"
};
let un = !1;
function Sa() {
  if (un) return;
  un = !0;
  const e = document.createElement("style");
  e.textContent = `
.fd-message-container {
  position: fixed;
  top: 16px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 99999;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  pointer-events: none;
}
.fd-message-item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
  font-size: 14px;
  color: #333;
  opacity: 0;
  transform: translateY(-8px);
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.fd-message-item--in {
  opacity: 1;
  transform: translateY(0);
}
`, document.head.appendChild(e);
}
function Oa() {
  let e = document.getElementById(dn);
  return e || (e = document.createElement("div"), e.id = dn, e.className = "fd-message-container", document.body.appendChild(e)), e;
}
function Bt(e, l, i = Ea) {
  if (typeof document > "u") return;
  Sa();
  const n = Oa(), s = document.createElement("div");
  s.className = "fd-message-item", s.innerHTML = `<span style="color:${Aa[e]};display:inline-flex;">${La[e]}</span><span></span>`, s.lastElementChild.textContent = l, n.appendChild(s), requestAnimationFrame(() => {
    s.classList.add("fd-message-item--in");
  }), setTimeout(() => {
    s.classList.remove("fd-message-item--in"), setTimeout(() => {
      s.remove(), n.childElementCount || n.remove();
    }, 220);
  }, i);
}
const cn = {
  success: (e, l) => Bt("success", e, l),
  error: (e, l) => Bt("error", e, l),
  info: (e, l) => Bt("info", e, l)
}, za = { class: "ding-join-marker__inner" }, Ba = { class: "ding-join-marker__name" }, Ua = { class: "ding-node-card__header" }, Va = { class: "ding-node-card__icon" }, Ra = { class: "ding-node-card__title" }, Fa = {
  key: 1,
  class: "ding-node-card__actions"
}, Ja = { class: "ding-node-card__body" }, Ya = {
  key: 0,
  class: "ding-node-card__members"
}, Wa = { class: "ding-node-card__member-mark" }, Ga = { class: "ding-node-card__member-name" }, Ha = /* @__PURE__ */ q({
  __name: "NodeCard",
  props: {
    node: {},
    typePrefix: {},
    viewer: { type: Boolean },
    highLight: {},
    theme: {},
    canDelete: { type: Boolean, default: !0 },
    depth: { default: 0 }
  },
  emits: ["edit", "delete"],
  setup(e) {
    const l = e, i = E(() => l.node.type.replace(l.typePrefix, "")), n = E(() => {
      switch (i.value) {
        case "task":
          return l.depth === 1 ? "申请人" : "审批人";
        case "custom":
          return "自定义节点";
        case "subProcess":
          return "子流程";
        default:
          return "任务";
      }
    }), s = E(() => {
      switch (i.value) {
        case "task":
          return "✓";
        case "custom":
          return "★";
        case "subProcess":
          return "▣";
        default:
          return "●";
      }
    }), c = E(() => {
      var j;
      return (j = l.highLight) != null && j.activeNodeNames ? l.highLight.activeNodeNames.includes(l.node.id) : !1;
    }), a = E(() => {
      var j;
      return (j = l.highLight) != null && j.historyNodeNames ? l.highLight.historyNodeNames.includes(l.node.id) : !1;
    }), r = E(() => c.value ? i.value === "start" || i.value === "end" ? "ding-node-pill--active" : "ding-node-card--active" : a.value ? i.value === "start" || i.value === "end" ? "ding-node-pill--history" : "ding-node-card--history" : ""), y = E(() => {
      var j, g, C, D;
      return ((j = l.node.properties) == null ? void 0 : j.performType) !== "ALL" ? "" : (((g = l.node.properties) == null ? void 0 : g.countersignType) || ((D = (C = l.node.properties) == null ? void 0 : C.field) == null ? void 0 : D.countersignType)) === "SEQUENTIAL" ? "SEQUENTIAL" : "PARALLEL";
    }), v = E(() => y.value === "SEQUENTIAL" ? "顺序会签" : y.value === "PARALLEL" ? "并行会签" : ""), h = E(() => y.value === "SEQUENTIAL" ? "ding-node-card--seq-countersign" : y.value === "PARALLEL" ? "ding-node-card--parallel-countersign" : ""), p = E(() => {
      var j, g, C;
      const D = (g = (j = l.highLight) == null ? void 0 : j.nodeProgress) == null ? void 0 : g[l.node.id];
      return (C = D == null ? void 0 : D.members) != null && C.length ? D.members.map((T) => ({
        id: T.id,
        name: T.name || T.id,
        done: !!T.done,
        active: !!T.active
      })) : [];
    }), f = E(() => {
      var j, g, C;
      return c.value && ((j = l.theme) != null && j.activeColor) ? { backgroundColor: l.theme.activeColor } : a.value && ((g = l.theme) != null && g.historyColor) ? { backgroundColor: l.theme.historyColor } : y.value === "SEQUENTIAL" ? { backgroundColor: "#fa8c16" } : y.value === "PARALLEL" ? { backgroundColor: "#1677ff" } : (C = l.theme) != null && C.primaryColor ? { backgroundColor: l.theme.primaryColor } : {};
    });
    return (j, g) => i.value === "start" ? (o(), u("div", {
      key: 0,
      class: ne(["ding-node-pill", "ding-node-pill--start", r.value, { "is-clickable": !e.viewer }]),
      onClick: g[0] || (g[0] = (C) => !e.viewer && j.$emit("edit", e.node))
    }, " 开始 ", 2)) : i.value === "end" ? (o(), u("div", {
      key: 1,
      class: ne(["ding-node-pill", "ding-node-pill--end", r.value, { "is-clickable": !e.viewer }]),
      onClick: g[1] || (g[1] = (C) => !e.viewer && j.$emit("edit", e.node))
    }, " 结束 ", 2)) : i.value === "join" ? (o(), u("div", {
      key: 2,
      class: ne(["ding-condition-group", "ding-join-marker", r.value, { "is-clickable": !e.viewer }]),
      onClick: g[2] || (g[2] = (C) => !e.viewer && j.$emit("edit", e.node))
    }, [
      g[6] || (g[6] = t("div", { class: "ding-condition-group__header" }, [
        t("span", { class: "ding-condition-group__title" }, "合并节点")
      ], -1)),
      t("div", za, [
        g[5] || (g[5] = t("span", { class: "ding-join-marker__dot" }, null, -1)),
        t("span", Ba, w(e.node.name || "合并点"), 1)
      ])
    ], 2)) : (o(), u("div", {
      key: 3,
      class: ne(["ding-node-card", r.value, h.value]),
      onClick: g[4] || (g[4] = (C) => j.$emit("edit", e.node))
    }, [
      t("div", {
        class: "ding-node-card__bar",
        style: ce(f.value)
      }, null, 4),
      t("div", Ua, [
        t("span", Va, w(s.value), 1),
        t("span", Ra, w(n.value), 1),
        v.value ? (o(), u("span", {
          key: 0,
          class: ne(["ding-node-card__badge", `ding-node-card__badge--${y.value}`])
        }, w(v.value), 3)) : M("", !0),
        e.viewer ? M("", !0) : (o(), u("span", Fa, [
          e.canDelete ? (o(), u("button", {
            key: 0,
            class: "ding-node-card__action-btn ding-node-card__action-btn--delete",
            onClick: g[3] || (g[3] = Se((C) => j.$emit("delete", e.node), ["stop"])),
            title: "删除"
          }, " × ")) : M("", !0)
        ]))
      ]),
      J(H(In), {
        title: e.node.name || "未命名节点"
      }, {
        default: te(() => [
          t("div", Ja, w(e.node.name || "未命名节点"), 1)
        ]),
        _: 1
      }, 8, ["title"]),
      p.value.length ? (o(), u("div", Ya, [
        (o(!0), u(G, null, le(p.value, (C) => (o(), u("div", {
          key: C.id,
          class: ne(["ding-node-card__member", { "is-done": C.done, "is-active": C.active }])
        }, [
          t("span", Wa, w(C.done ? "✓" : C.active ? "▶" : "·"), 1),
          t("span", Ga, w(C.name), 1)
        ], 2))), 128))
      ])) : M("", !0)
    ], 2));
  }
}), Ka = {
  key: 0,
  class: "ding-node-selector"
}, Qa = ["onClick"], Xa = /* @__PURE__ */ q({
  __name: "NodeSelector",
  props: {
    visible: { type: Boolean },
    dndPanel: {},
    typePrefix: {}
  },
  emits: ["select", "update:visible"],
  setup(e, { emit: l }) {
    const i = e, n = l, s = b(null), c = E(() => i.dndPanel ? i.dndPanel.filter((g) => {
      if (!g.type || g.hide) return !1;
      const C = g.type.replace(i.typePrefix, "");
      return !["start", "end", "decision", "fork", "join"].includes(C);
    }) : []);
    function a(g) {
      if (!g.type) return "";
      switch (g.type.replace(i.typePrefix, "")) {
        case "task":
          return "ding-node-selector__item__icon--task";
        case "custom":
          return "ding-node-selector__item__icon--custom";
        case "subProcess":
          return "ding-node-selector__item__icon--subprocess";
        default:
          return "ding-node-selector__item__icon--task";
      }
    }
    function r(g) {
      if (!g.type) return "?";
      switch (g.type.replace(i.typePrefix, "")) {
        case "task":
          return "✓";
        case "custom":
          return "★";
        case "subProcess":
          return "▣";
        default:
          return "✓";
      }
    }
    function y(g) {
      if (!g.type) return "未知";
      switch (g.type.replace(i.typePrefix, "")) {
        case "task":
          return "审批节点";
        case "custom":
          return "自定义节点";
        case "subProcess":
          return "子流程";
        default:
          return g.type;
      }
    }
    function v(g) {
      g.type && n("select", g.type), f();
    }
    function h() {
      n("select", "__condition__"), f();
    }
    function p() {
      n("select", "__parallel__"), f();
    }
    function f() {
      n("update:visible", !1);
    }
    function j(g) {
      var C;
      if (!i.visible) return;
      const D = g.target;
      D && ((C = s.value) != null && C.contains(D) || f());
    }
    return he(() => document.addEventListener("click", j)), We(() => document.removeEventListener("click", j)), (g, C) => e.visible ? (o(), u("div", Ka, [
      t("div", {
        ref_key: "panelRef",
        ref: s,
        class: "ding-node-selector__panel"
      }, [
        (o(!0), u(G, null, le(c.value, (D) => (o(), u("div", {
          key: D.type,
          class: "ding-node-selector__item",
          onClick: (T) => v(D)
        }, [
          t("span", {
            class: ne(["ding-node-selector__item__icon", a(D)])
          }, w(r(D)), 3),
          t("span", null, w(D.label || D.text || y(D)), 1)
        ], 8, Qa))), 128)),
        t("div", {
          class: "ding-node-selector__item",
          onClick: h
        }, [...C[0] || (C[0] = [
          t("span", { class: "ding-node-selector__item__icon ding-node-selector__item__icon--condition" }, " ✦ ", -1),
          t("span", null, "条件分支", -1)
        ])]),
        t("div", {
          class: "ding-node-selector__item",
          onClick: p
        }, [...C[1] || (C[1] = [
          t("span", { class: "ding-node-selector__item__icon ding-node-selector__item__icon--parallel" }, " ≣ ", -1),
          t("span", null, "并行分支", -1)
        ])])
      ], 512)
    ])) : M("", !0);
  }
}), qa = {
  key: 0,
  class: "ding-add-btn"
}, Za = {
  key: 1,
  class: "ding-add-btn ding-add-btn--readonly"
}, es = {
  key: 2,
  class: "ding-add-btn"
}, Xt = /* @__PURE__ */ q({
  __name: "AddButton",
  props: {
    viewer: { type: Boolean },
    typePrefix: {},
    dndPanel: {},
    readonly: { type: Boolean, default: !1 },
    prevNodeId: { default: void 0 },
    nextNodeId: { default: void 0 },
    highLight: {}
  },
  emits: ["add"],
  setup(e, { emit: l }) {
    const i = e, n = E(() => {
      if (!i.highLight || !i.prevNodeId || !i.nextNodeId) return "default";
      const v = i.highLight.activeNodeNames || [], h = i.highLight.historyNodeNames || [];
      return v.length && h.includes(i.prevNodeId) && v.includes(i.nextNodeId) ? "active" : h.includes(i.prevNodeId) && h.includes(i.nextNodeId) ? "history" : "default";
    }), s = E(() => {
      const v = n.value;
      return v === "default" ? "" : `ding-line-vertical--${v}`;
    }), c = l, a = b(!1);
    function r() {
      a.value = !a.value;
    }
    function y(v) {
      c("add", v), a.value = !1;
    }
    return (v, h) => !e.viewer && !e.readonly ? (o(), u("div", qa, [
      t("div", {
        class: ne(["ding-line-vertical", s.value])
      }, null, 2),
      t("button", {
        class: "ding-add-btn__circle",
        onClick: Se(r, ["stop"])
      }, "+"),
      t("div", {
        class: ne(["ding-line-vertical", s.value])
      }, null, 2),
      J(Xa, {
        visible: a.value,
        "dnd-panel": e.dndPanel,
        "type-prefix": e.typePrefix,
        "onUpdate:visible": h[0] || (h[0] = (p) => a.value = p),
        onSelect: y
      }, null, 8, ["visible", "dnd-panel", "type-prefix"])
    ])) : !e.viewer && e.readonly ? (o(), u("div", Za, [
      t("div", {
        class: ne(["ding-line-vertical ding-line-vertical--short", s.value])
      }, null, 2)
    ])) : (o(), u("div", es, [
      t("div", {
        class: ne(["ding-line-vertical", s.value])
      }, null, 2)
    ]));
  }
}), ts = { class: "ding-branch-col" }, ns = ["title"], ls = { class: "ding-branch-col__head-text" }, as = {
  key: 0,
  class: "ding-branch-col__head-edit",
  title: "编辑分支"
}, ss = { class: "ding-branch-col__content" }, os = /* @__PURE__ */ q({
  __name: "BranchColumn",
  props: {
    branch: {},
    typePrefix: {},
    viewer: { type: Boolean },
    highLight: {},
    theme: {},
    dndPanel: {},
    canDeleteChecker: { type: Function }
  },
  emits: ["edit", "delete", "add", "add-branch", "edit-branch", "add-to-branch"],
  setup(e, { emit: l }) {
    const i = e, n = l;
    function s() {
      i.viewer || n("edit-branch", i.branch);
    }
    return (c, a) => (o(), u("div", ts, [
      a[6] || (a[6] = t("div", { class: "ding-branch-col__line-top" }, null, -1)),
      e.branch.name || !e.viewer ? (o(), u("div", {
        key: 0,
        class: "ding-branch-col__head",
        title: e.branch.name || "点击编辑",
        onClick: s
      }, [
        t("span", ls, w(e.branch.name || "未命名"), 1),
        e.viewer ? M("", !0) : (o(), u("span", as, " ✎ "))
      ], 8, ns)) : M("", !0),
      t("div", ss, [
        e.branch.children ? (o(), ae(Tt, {
          key: 0,
          node: e.branch.children,
          "type-prefix": e.typePrefix,
          viewer: e.viewer,
          "high-light": e.highLight,
          theme: e.theme,
          "dnd-panel": e.dndPanel,
          "can-delete-checker": e.canDeleteChecker,
          onEdit: a[0] || (a[0] = (r) => c.$emit("edit", r)),
          onDelete: a[1] || (a[1] = (r) => c.$emit("delete", r)),
          onAdd: a[2] || (a[2] = (r, y) => c.$emit("add", r, y)),
          onAddBranch: a[3] || (a[3] = (r) => c.$emit("add-branch", r)),
          onEditBranch: a[4] || (a[4] = (r) => c.$emit("edit-branch", r))
        }, null, 8, ["node", "type-prefix", "viewer", "high-light", "theme", "dnd-panel", "can-delete-checker"])) : (o(), ae(Xt, {
          key: 1,
          viewer: e.viewer,
          "type-prefix": e.typePrefix,
          "dnd-panel": e.dndPanel,
          onAdd: a[5] || (a[5] = (r) => c.$emit("add-to-branch", r, e.branch))
        }, null, 8, ["viewer", "type-prefix", "dnd-panel"]))
      ]),
      a[7] || (a[7] = t("div", { class: "ding-branch-col__line-bottom" }, null, -1))
    ]));
  }
}), is = { class: "ding-condition-group" }, rs = { class: "ding-condition-group__header" }, ds = ["title"], us = /* @__PURE__ */ q({
  __name: "ConditionGroup",
  props: {
    node: {},
    typePrefix: {},
    viewer: { type: Boolean },
    highLight: {},
    theme: {},
    dndPanel: {},
    protectedIds: { default: () => /* @__PURE__ */ new Set() },
    canDeleteChecker: {}
  },
  emits: ["edit", "delete", "add", "add-branch", "edit-branch", "add-to-branch"],
  setup(e) {
    const l = e, i = E(() => l.protectedIds ?? /* @__PURE__ */ new Set()), n = b(), s = b("0px"), c = b("0px");
    let a = null;
    function r() {
      if (!n.value) return;
      const h = n.value, p = h.querySelectorAll(".ding-branch-col");
      if (p.length < 2) {
        s.value = "0px";
        return;
      }
      const f = p[0], j = p[p.length - 1], g = h.getBoundingClientRect(), C = f.getBoundingClientRect().left + f.offsetWidth / 2 - g.left, D = j.getBoundingClientRect().left + j.offsetWidth / 2 - g.left;
      s.value = `${D - C}px`, c.value = `${C}px`;
    }
    const y = E(() => ({
      width: s.value,
      left: c.value
    })), v = E(() => ({
      width: s.value,
      left: c.value
    }));
    return he(() => {
      tt(() => {
        r(), n.value && typeof ResizeObserver < "u" && (a = new ResizeObserver(() => r()), a.observe(n.value));
      });
    }), We(() => {
      a == null || a.disconnect();
    }), be(() => l.node.branches.length, () => {
      tt(r);
    }), (h, p) => (o(), u("div", is, [
      t("div", rs, [
        t("span", {
          class: ne(["ding-condition-group__title", { "ding-condition-group__title--clickable": !e.viewer }]),
          title: e.viewer ? "" : "点击编辑决策配置",
          onClick: p[0] || (p[0] = (f) => !e.viewer && h.$emit("edit", e.node))
        }, "条件分支", 10, ds),
        e.viewer ? M("", !0) : (o(), u("span", {
          key: 0,
          class: "ding-condition-group__add-branch",
          onClick: p[1] || (p[1] = (f) => h.$emit("add-branch", e.node))
        }, " + 添加条件 ")),
        !e.viewer && !i.value.has(e.node.id) ? (o(), u("button", {
          key: 1,
          class: "ding-condition-group__delete",
          title: "删除整个条件分支组",
          onClick: p[2] || (p[2] = (f) => h.$emit("delete", e.node))
        }, "×")) : M("", !0)
      ]),
      t("div", {
        class: "ding-condition-group__branches",
        ref_key: "branchesRef",
        ref: n
      }, [
        t("div", {
          class: "ding-condition-group__top-line",
          style: ce(y.value)
        }, null, 4),
        (o(!0), u(G, null, le(e.node.branches, (f, j) => (o(), ae(os, {
          key: f.id,
          branch: f,
          "type-prefix": e.typePrefix,
          viewer: e.viewer,
          "high-light": e.highLight,
          theme: e.theme,
          "dnd-panel": e.dndPanel,
          "can-delete-checker": e.canDeleteChecker,
          onEdit: p[3] || (p[3] = (g) => h.$emit("edit", g)),
          onDelete: p[4] || (p[4] = (g) => h.$emit("delete", g)),
          onAdd: (g, C) => h.$emit("add", g, C, j),
          onAddBranch: p[5] || (p[5] = (g) => h.$emit("add-branch", g)),
          onEditBranch: p[6] || (p[6] = (g) => h.$emit("edit-branch", g)),
          onAddToBranch: p[7] || (p[7] = (g, C) => h.$emit("add-to-branch", g, C))
        }, null, 8, ["branch", "type-prefix", "viewer", "high-light", "theme", "dnd-panel", "can-delete-checker", "onAdd"]))), 128)),
        t("div", {
          class: "ding-condition-group__bottom-line",
          style: ce(v.value)
        }, null, 4)
      ], 512)
    ]));
  }
}), cs = { class: "ding-condition-group ding-parallel-group" }, fs = { class: "ding-condition-group__header" }, ps = {
  key: 0,
  class: "ding-branch-col__head ding-branch-col__head--static"
}, vs = { class: "ding-branch-col__head-text" }, ms = { class: "ding-branch-col__content" }, hs = {
  key: 0,
  class: "ding-branch-col__empty"
}, ys = {
  key: 0,
  class: "ding-line-vertical"
}, gs = /* @__PURE__ */ q({
  __name: "ParallelGroup",
  props: {
    node: {},
    typePrefix: {},
    viewer: { type: Boolean },
    highLight: {},
    theme: {},
    dndPanel: {},
    protectedIds: { default: () => /* @__PURE__ */ new Set() },
    canDeleteChecker: {}
  },
  emits: ["edit", "delete", "add", "add-branch", "edit-branch", "add-to-branch"],
  setup(e, { emit: l }) {
    const i = e, n = E(() => i.protectedIds ?? /* @__PURE__ */ new Set()), s = b(), c = b("0px"), a = b("0px");
    function r() {
      if (!s.value) return;
      const h = s.value, p = h.querySelectorAll(".ding-branch-col");
      if (p.length < 2) {
        c.value = "0px";
        return;
      }
      const f = p[0], j = p[p.length - 1], g = h.getBoundingClientRect(), C = f.getBoundingClientRect().left + f.offsetWidth / 2 - g.left, D = j.getBoundingClientRect().left + j.offsetWidth / 2 - g.left;
      c.value = `${D - C}px`, a.value = `${C}px`;
    }
    const y = E(() => ({
      width: c.value,
      left: a.value
    })), v = E(() => ({
      width: c.value,
      left: a.value
    }));
    return he(() => {
      tt(r);
    }), be(() => i.node.branches.length, () => {
      tt(r);
    }), (h, p) => (o(), u("div", cs, [
      t("div", fs, [
        p[13] || (p[13] = t("span", { class: "ding-condition-group__title" }, "并行分支", -1)),
        e.viewer ? M("", !0) : (o(), u("span", {
          key: 0,
          class: "ding-condition-group__add-branch",
          onClick: p[0] || (p[0] = (f) => h.$emit("add-branch", e.node))
        }, " + 添加分支 ")),
        !e.viewer && !n.value.has(e.node.id) ? (o(), u("button", {
          key: 1,
          class: "ding-condition-group__delete",
          title: "删除整个并行分支组",
          onClick: p[1] || (p[1] = (f) => h.$emit("delete", e.node))
        }, "×")) : M("", !0)
      ]),
      t("div", {
        class: "ding-condition-group__branches",
        ref_key: "branchesRef",
        ref: s
      }, [
        t("div", {
          class: "ding-condition-group__top-line",
          style: ce(y.value)
        }, null, 4),
        (o(!0), u(G, null, le(e.node.branches, (f, j) => (o(), u("div", {
          key: f.id,
          class: "ding-branch-col"
        }, [
          p[15] || (p[15] = t("div", { class: "ding-branch-col__line-top" }, null, -1)),
          e.viewer ? M("", !0) : (o(), u("div", ps, [
            t("span", vs, "分支 " + w(j + 1), 1)
          ])),
          t("div", ms, [
            f.children ? (o(), ae(Tt, {
              key: 0,
              node: f.children,
              "type-prefix": e.typePrefix,
              viewer: e.viewer,
              "high-light": e.highLight,
              theme: e.theme,
              "dnd-panel": e.dndPanel,
              "can-delete-checker": e.canDeleteChecker,
              onEdit: p[2] || (p[2] = (g) => h.$emit("edit", g)),
              onDelete: p[3] || (p[3] = (g) => h.$emit("delete", g)),
              onAdd: p[4] || (p[4] = (g, C) => h.$emit("add", g, C)),
              onAddBranch: p[5] || (p[5] = (g) => h.$emit("add-branch", g)),
              onEditBranch: p[6] || (p[6] = (g) => h.$emit("edit-branch", g))
            }, null, 8, ["node", "type-prefix", "viewer", "high-light", "theme", "dnd-panel", "can-delete-checker"])) : (o(), u(G, { key: 1 }, [
              e.viewer ? M("", !0) : (o(), u("div", hs, [
                p[14] || (p[14] = t("div", { class: "ding-branch-col__empty-hint" }, "点击 + 添加任务节点", -1)),
                J(Xt, {
                  viewer: e.viewer,
                  "type-prefix": e.typePrefix,
                  "dnd-panel": e.dndPanel,
                  onAdd: (g) => h.$emit("add-to-branch", g, f)
                }, null, 8, ["viewer", "type-prefix", "dnd-panel", "onAdd"])
              ]))
            ], 64))
          ]),
          p[16] || (p[16] = t("div", { class: "ding-branch-col__line-bottom" }, null, -1))
        ]))), 128)),
        t("div", {
          class: "ding-condition-group__bottom-line",
          style: ce(v.value)
        }, null, 4)
      ], 512),
      e.node.joinChildren ? (o(), u("div", ys)) : M("", !0),
      e.node.joinChildren ? (o(), ae(Tt, {
        key: 1,
        node: e.node.joinChildren,
        "type-prefix": e.typePrefix,
        viewer: e.viewer,
        "high-light": e.highLight,
        theme: e.theme,
        "dnd-panel": e.dndPanel,
        "can-delete-checker": e.canDeleteChecker,
        onEdit: p[7] || (p[7] = (f) => h.$emit("edit", f)),
        onDelete: p[8] || (p[8] = (f) => h.$emit("delete", f)),
        onAdd: p[9] || (p[9] = (f, j) => h.$emit("add", f, j)),
        onAddBranch: p[10] || (p[10] = (f) => h.$emit("add-branch", f)),
        onEditBranch: p[11] || (p[11] = (f) => h.$emit("edit-branch", f)),
        onAddToBranch: p[12] || (p[12] = (f, j) => h.$emit("add-to-branch", f, j))
      }, null, 8, ["node", "type-prefix", "viewer", "high-light", "theme", "dnd-panel", "can-delete-checker"])) : M("", !0)
    ]));
  }
}), bs = /* @__PURE__ */ Me(gs, [["__scopeId", "data-v-3821858c"]]), ks = { class: "ding-node-chain" }, Tt = /* @__PURE__ */ q({
  __name: "NodeChain",
  props: {
    node: {},
    typePrefix: {},
    viewer: { type: Boolean },
    highLight: {},
    theme: {},
    dndPanel: {},
    protectedIds: { default: () => /* @__PURE__ */ new Set() },
    canDeleteChecker: {},
    depth: { default: 0 }
  },
  emits: ["edit", "delete", "add", "add-branch", "edit-branch", "add-to-branch"],
  setup(e) {
    const l = e, i = E(() => l.protectedIds ?? /* @__PURE__ */ new Set()), n = E(
      () => l.canDeleteChecker ?? ((y) => !0)
    );
    function s(y) {
      return !(i.value.has(y.id) || !n.value(y));
    }
    const c = E(() => Ce(l.node)), a = E(() => Ie(l.node)), r = E(() => c.value ? "condition" : a.value ? "fork" : l.node.type.replace(l.typePrefix, ""));
    return (y, v) => {
      var h;
      const p = Zn("NodeChain", !0);
      return o(), u("div", ks, [
        a.value ? (o(), ae(bs, {
          key: 0,
          node: e.node,
          "type-prefix": e.typePrefix,
          viewer: e.viewer,
          "high-light": e.highLight,
          theme: e.theme,
          "dnd-panel": e.dndPanel,
          "protected-ids": i.value,
          "can-delete-checker": n.value,
          onEdit: v[0] || (v[0] = (f) => y.$emit("edit", f)),
          onDelete: v[1] || (v[1] = (f) => y.$emit("delete", f)),
          onAdd: v[2] || (v[2] = (f, j) => y.$emit("add", f, j)),
          onAddBranch: v[3] || (v[3] = (f) => y.$emit("add-branch", f)),
          onEditBranch: v[4] || (v[4] = (f) => y.$emit("edit-branch", f)),
          onAddToBranch: v[5] || (v[5] = (f, j) => y.$emit("add-to-branch", f, j))
        }, null, 8, ["node", "type-prefix", "viewer", "high-light", "theme", "dnd-panel", "protected-ids", "can-delete-checker"])) : c.value ? (o(), ae(us, {
          key: 1,
          node: e.node,
          "type-prefix": e.typePrefix,
          viewer: e.viewer,
          "high-light": e.highLight,
          theme: e.theme,
          "dnd-panel": e.dndPanel,
          "protected-ids": i.value,
          "can-delete-checker": n.value,
          onEdit: v[6] || (v[6] = (f) => y.$emit("edit", f)),
          onDelete: v[7] || (v[7] = (f) => y.$emit("delete", f)),
          onAdd: v[8] || (v[8] = (f, j) => y.$emit("add", f, j)),
          onAddBranch: v[9] || (v[9] = (f) => y.$emit("add-branch", f)),
          onEditBranch: v[10] || (v[10] = (f) => y.$emit("edit-branch", f)),
          onAddToBranch: v[11] || (v[11] = (f, j) => y.$emit("add-to-branch", f, j))
        }, null, 8, ["node", "type-prefix", "viewer", "high-light", "theme", "dnd-panel", "protected-ids", "can-delete-checker"])) : (o(), ae(Ha, {
          key: 2,
          node: e.node,
          "type-prefix": e.typePrefix,
          viewer: e.viewer,
          "high-light": e.highLight,
          theme: e.theme,
          depth: e.depth,
          "can-delete": s(e.node),
          onEdit: v[12] || (v[12] = (f) => y.$emit("edit", f)),
          onDelete: v[13] || (v[13] = (f) => y.$emit("delete", f))
        }, null, 8, ["node", "type-prefix", "viewer", "high-light", "theme", "depth", "can-delete"])),
        !a.value && r.value !== "end" ? (o(), ae(Xt, {
          key: 3,
          viewer: e.viewer,
          "type-prefix": e.typePrefix,
          "dnd-panel": e.dndPanel,
          readonly: r.value === "start",
          "prev-node-id": e.node.id,
          "next-node-id": (h = e.node.children) == null ? void 0 : h.id,
          "high-light": e.highLight,
          onAdd: v[14] || (v[14] = (f) => y.$emit("add", f, e.node))
        }, null, 8, ["viewer", "type-prefix", "dnd-panel", "readonly", "prev-node-id", "next-node-id", "high-light"])) : M("", !0),
        !a.value && e.node.children ? (o(), ae(p, {
          key: 4,
          node: e.node.children,
          "type-prefix": e.typePrefix,
          viewer: e.viewer,
          "high-light": e.highLight,
          theme: e.theme,
          "dnd-panel": e.dndPanel,
          depth: e.depth + 1,
          "protected-ids": i.value,
          "can-delete-checker": n.value,
          onEdit: v[15] || (v[15] = (f) => y.$emit("edit", f)),
          onDelete: v[16] || (v[16] = (f) => y.$emit("delete", f)),
          onAdd: v[17] || (v[17] = (f, j) => y.$emit("add", f, j)),
          onAddBranch: v[18] || (v[18] = (f) => y.$emit("add-branch", f)),
          onEditBranch: v[19] || (v[19] = (f) => y.$emit("edit-branch", f)),
          onAddToBranch: v[20] || (v[20] = (f, j) => y.$emit("add-to-branch", f, j))
        }, null, 8, ["node", "type-prefix", "viewer", "high-light", "theme", "dnd-panel", "depth", "protected-ids", "can-delete-checker"])) : M("", !0)
      ]);
    };
  }
}), js = ["title"], $s = {
  key: 0,
  xmlns: "http://www.w3.org/2000/svg",
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  "stroke-width": "2",
  "stroke-linecap": "round",
  "stroke-linejoin": "round",
  width: "20",
  height: "20"
}, ws = {
  key: 1,
  xmlns: "http://www.w3.org/2000/svg",
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  "stroke-width": "2",
  "stroke-linecap": "round",
  "stroke-linejoin": "round",
  width: "20",
  height: "20"
}, _s = ["title", "onClick"], Cs = { class: "ding-control-panel__text" }, Is = /* @__PURE__ */ q({
  __name: "ControlPanel",
  props: {
    initControl: {
      type: Boolean,
      default: !0
    },
    control: {
      type: Array
    },
    viewer: {
      type: Boolean,
      default: !1
    }
  },
  emits: ["save", "clear", "view-data", "import-data", "fullscreen"],
  setup(e, { emit: l }) {
    const i = e, n = l, s = b(!1), c = b(!1);
    function a() {
      const D = typeof window < "u" && window.innerWidth < 768, T = typeof document < "u" && document.documentElement.classList.contains("is-mobile-preview"), N = D || T;
      s.value = N, N || (c.value = !1);
    }
    function r() {
      a();
    }
    function y() {
      c.value = !c.value;
    }
    function v() {
      c.value = !1;
    }
    function h() {
      s.value && c.value && v();
    }
    let p = null;
    he(() => {
      a(), window.addEventListener("resize", r), document.addEventListener("click", h), p = new MutationObserver(a), p.observe(document.documentElement, {
        attributes: !0,
        attributeFilter: ["class"]
      });
    }), We(() => {
      window.removeEventListener("resize", r), document.removeEventListener("click", h), p == null || p.disconnect(), p = null;
    });
    const f = [
      {
        key: "save",
        iconClass: "ding-icon-save",
        title: "保存",
        text: "保存",
        sort: 90
      },
      {
        key: "clear",
        iconClass: "ding-icon-clear",
        title: "清空",
        text: "清空",
        sort: 60
      },
      {
        key: "see",
        iconClass: "ding-icon-see",
        title: "查看数据",
        text: "查看数据",
        sort: 70
      },
      {
        key: "import",
        iconClass: "ding-icon-import",
        title: "导入",
        text: "导入",
        sort: 80
      },
      {
        key: "fullscreen",
        iconClass: "ding-icon-fullscreen",
        title: "全屏",
        text: "全屏",
        sort: 100
      }
    ], j = E(() => {
      if (!i.initControl) return i.control || [];
      let D = [...f];
      if (i.control && i.control.length > 0)
        for (const T of i.control) {
          const N = D.findIndex((U) => U.key === T.key);
          N >= 0 ? D[N] = { ...D[N], ...T } : D.push(T);
        }
      return D;
    }), g = E(() => {
      let D = j.value.filter((T) => !T.hide);
      return i.viewer && (D = D.filter((T) => !["save", "clear", "import"].includes(T.key || ""))), D.sort((T, N) => (T.sort || 0) - (N.sort || 0));
    });
    function C(D) {
      if (s.value && v(), D.onClick && typeof D.onClick == "function") {
        D.onClick(D);
        return;
      }
      switch (D.key) {
        case "save":
          n("save");
          break;
        case "clear":
          n("clear");
          break;
        case "see":
          n("view-data");
          break;
        case "import":
          n("import-data");
          break;
        case "fullscreen":
          n("fullscreen");
          break;
      }
    }
    return (D, T) => (o(), u("div", {
      class: ne(["ding-control-panel", { "is-mobile": s.value, "is-mobile-open": s.value && c.value }])
    }, [
      s.value ? (o(), u("button", {
        key: 0,
        class: "ding-control-panel__mobile-toggle",
        title: c.value ? "收起操作" : "展开操作",
        onClick: Se(y, ["stop"])
      }, [
        c.value ? (o(), u("svg", ws, [...T[2] || (T[2] = [
          t("line", {
            x1: "18",
            y1: "6",
            x2: "6",
            y2: "18"
          }, null, -1),
          t("line", {
            x1: "6",
            y1: "6",
            x2: "18",
            y2: "18"
          }, null, -1)
        ])])) : (o(), u("svg", $s, [...T[1] || (T[1] = [
          t("line", {
            x1: "3",
            y1: "6",
            x2: "21",
            y2: "6"
          }, null, -1),
          t("line", {
            x1: "3",
            y1: "12",
            x2: "21",
            y2: "12"
          }, null, -1),
          t("line", {
            x1: "3",
            y1: "18",
            x2: "21",
            y2: "18"
          }, null, -1)
        ])]))
      ], 8, js)) : M("", !0),
      g.value.length > 0 && (!s.value || c.value) ? (o(), u("div", {
        key: 1,
        class: "ding-control-panel__list",
        onClick: T[0] || (T[0] = Se(() => {
        }, ["stop"]))
      }, [
        (o(!0), u(G, null, le(g.value, (N) => (o(), u("div", {
          key: N.key,
          class: "ding-control-panel__item",
          title: N.title || N.text,
          onClick: (U) => C(N)
        }, [
          t("span", {
            class: ne(["ding-control-panel__icon", N.iconClass])
          }, null, 2),
          t("span", Cs, w(N.text), 1)
        ], 8, _s))), 128))
      ])) : M("", !0)
    ], 2));
  }
}), xs = {
  labelWidth: "120px",
  formItems: [{
    name: "name",
    label: "唯一编码",
    component: "Input",
    componentProps: {
      placeholder: "请输入唯一编码"
    }
  }, {
    name: "preInterceptors",
    label: "前置拦截器",
    component: "Input",
    componentProps: {
      placeholder: "请输入前置拦截器"
    }
  }, {
    name: "postInterceptors",
    label: "后置拦截器",
    component: "Input",
    componentProps: {
      placeholder: "请输入后置拦截器"
    }
  }]
}, Ds = {
  labelWidth: "120px",
  formItems: [{
    name: "name",
    label: "唯一编码",
    component: "Input",
    componentProps: {
      placeholder: "请输入唯一编码"
    }
  }, {
    name: "preInterceptors",
    label: "前置拦截器",
    component: "Input",
    componentProps: {
      placeholder: "请输入前置拦截器"
    }
  }, {
    name: "postInterceptors",
    label: "后置拦截器",
    component: "Input",
    componentProps: {
      placeholder: "请输入后置拦截器"
    }
  }]
}, Ns = {
  labelWidth: "120px",
  formItems: [
    {
      name: "name",
      label: "唯一编码",
      component: "Input",
      componentProps: {
        placeholder: "请输入唯一编码"
      }
    },
    {
      name: "displayName",
      label: "显示名称",
      component: "Input",
      componentProps: {
        placeholder: "请输入显示名称"
      }
    },
    {
      name: "preInterceptors",
      label: "前置拦截器",
      component: "Input",
      componentProps: {
        placeholder: "请输入前置拦截器"
      }
    },
    {
      name: "postInterceptors",
      label: "后置拦截器",
      component: "Input",
      componentProps: {
        placeholder: "请输入后置拦截器"
      }
    },
    {
      name: "form",
      label: "表单",
      component: "Input",
      componentProps: {
        placeholder: "请输入表单"
      }
    },
    {
      name: "assignee",
      label: "参与人",
      component: "Input",
      componentProps: {
        placeholder: "请输入参与人"
      }
    },
    {
      name: "assignmentHandler",
      label: "参与人处理类",
      component: "Input",
      componentProps: {
        placeholder: "请输入参与人处理类"
      }
    },
    {
      name: "candidateUsers",
      label: "候选用户",
      component: "Input",
      helpMessage: "多个用户用英文逗号分隔",
      componentProps: {
        placeholder: "请输入候选用户（多个用逗号分隔）"
      }
    },
    {
      name: "candidateGroups",
      label: "候选用户组",
      component: "Input",
      helpMessage: "多个用户组用英文逗号分隔",
      componentProps: {
        placeholder: "请输入候选用户组（多个用逗号分隔）"
      }
    },
    {
      name: "candidateHandler",
      label: "候选用户处理类",
      component: "Input",
      componentProps: {
        placeholder: "请输入候选用户处理类"
      }
    },
    {
      name: "taskType",
      label: "任务类型",
      component: "Select",
      componentProps: {
        placeholder: "请选择任务类型",
        options: [
          {
            label: "主办",
            value: "Major"
          },
          {
            label: "协办",
            value: "Aidant"
          }
        ]
      }
    },
    {
      name: "performType",
      label: "参与类型",
      component: "Select",
      componentProps: {
        placeholder: "请选择参与类型",
        options: [
          {
            label: "普通参与",
            value: "ANY"
          },
          {
            label: "会签参与",
            value: "ALL"
          }
        ]
      }
    },
    {
      name: "countersignType",
      label: "会签类型",
      component: "Select",
      defaultValue: "PARALLEL",
      helpMessage: "参与类型为会签参与时生效",
      componentProps: {
        placeholder: "请选择会签类型",
        options: [
          {
            label: "并行会签",
            value: "PARALLEL"
          },
          {
            label: "顺序会签",
            value: "SEQUENTIAL"
          }
        ]
      }
    },
    {
      name: "countersignCompletionCondition",
      label: "会签完成条件",
      component: "Input",
      helpMessage: "参与类型为会签参与时生效，如：nrOfCompletedInstances/nrOfInstances >= 0.6",
      componentProps: {
        placeholder: "请输入会签完成条件"
      }
    },
    {
      name: "actionBtns",
      label: "操作按钮",
      component: "Input",
      helpMessage: [
        "多个按钮用英文逗号分隔，普通参与可选：AGREE(同意)/REJECT(拒绝)/ROLLBACK(退回上一步)/ROLLBACK_TO_OPERATOR(退回发起人)/JUMP(跳转)",
        "会签参与可选：AGREE(同意)/COUNTERSIGN_DISAGREE(会签不同意)/ADD_CANDIDATE(加签)"
      ],
      componentProps: {
        placeholder: "如 AGREE,REJECT,ROLLBACK"
      }
    },
    {
      name: "reminderTime",
      label: "提醒时间",
      component: "Input",
      componentProps: {
        placeholder: "请输入提醒时间"
      }
    },
    {
      name: "reminderRepeat",
      label: "重复提醒间隔",
      component: "Input",
      componentProps: {
        placeholder: "请输入重复提醒间隔"
      }
    },
    {
      name: "expireTime",
      label: "期待完成时间",
      component: "Input",
      componentProps: {
        placeholder: "请输入期待完成时间"
      }
    },
    {
      name: "autoExecute",
      label: "是否自动完成",
      component: "Select",
      componentProps: {
        placeholder: "请选择是否自动完成",
        options: [
          {
            label: "是",
            value: "Y"
          },
          {
            label: "否",
            value: "N"
          }
        ]
      }
    },
    {
      name: "callback",
      label: "回调处理",
      component: "Input",
      componentProps: {
        placeholder: "请输入回调处理"
      }
    }
  ]
}, fn = {
  labelWidth: "130px",
  formItems: [{
    name: "name",
    label: "流程定义唯一编码",
    component: "Input",
    componentProps: {
      placeholder: "请输入流程定义唯一编码"
    }
  }, {
    name: "displayName",
    label: "流程定义显示名称",
    component: "Input",
    componentProps: {
      placeholder: "请输入流程定义显示名称"
    }
  }, {
    name: "expireTime",
    label: "期望完成时间",
    component: "Input",
    componentProps: {
      placeholder: "请输入期望完成时间"
    }
  }, {
    name: "instanceUrl",
    label: "实例启动表单",
    component: "Input",
    helpMessage: "如果为元数据表单，数据模型的表名称和流程唯一编码要保持一致",
    componentProps: {
      placeholder: "请输入实例启动表单"
    }
  }, {
    name: "enableFieldPerm",
    label: "启用字段权限",
    component: "Select",
    defaultValue: 0,
    helpMessage: "开启后，可在任务节点配置字段只读/可编辑/不可见",
    componentProps: {
      placeholder: "请选择是否启用字段权限",
      options: [
        {
          label: "否",
          value: 0
        },
        {
          label: "是",
          value: 1
        }
      ]
    }
  }, {
    name: "instanceNoClass",
    label: "实例编号生成类",
    component: "Input",
    componentProps: {
      placeholder: "请输入实例编号生成类"
    }
  }, {
    name: "preInterceptors",
    label: "前置拦截器",
    component: "Input",
    componentProps: {
      placeholder: "请输入前置拦截器"
    }
  }, {
    name: "postInterceptors",
    label: "后置拦截器",
    component: "Input",
    componentProps: {
      placeholder: "请输入后置拦截器"
    }
  }, {
    name: "relTableName",
    label: "关联业务表",
    component: "Input",
    helpMessage: "流程结束后业务数据落库的目标表；为空时使用流程唯一编码",
    componentProps: {
      placeholder: "如 biz_leave"
    }
  }, {
    name: "persistMode",
    label: "持久化模式",
    component: "Select",
    defaultValue: "ARCHIVE",
    helpMessage: "ARCHIVE=结束归档（默认）；SYNC=同步演进（发起写入、节点更新、结束定稿）。需配合后置拦截器 PersistPostInterceptor 使用",
    componentProps: {
      placeholder: "请选择持久化模式",
      options: [
        {
          label: "归档",
          value: "ARCHIVE"
        },
        {
          label: "同步",
          value: "SYNC"
        }
      ]
    }
  }, {
    name: "selectUserOnInitiate",
    label: "是否发起时选人",
    component: "Select",
    defaultValue: 0,
    componentProps: {
      placeholder: "请选择是否发起时选人",
      options: [
        {
          label: "否",
          value: 0
        },
        {
          label: "是",
          value: 1
        }
      ]
    }
  }, {
    name: "selectUserApi",
    label: "选人接口地址",
    component: "Input",
    helpMessage: '发起时选人为"是"时生效；目前仅支持POST请求，和通用下拉接口规范一致',
    componentProps: {
      placeholder: "请输入选人接口地址"
    }
  }, {
    name: "enableCcActors",
    label: "启用抄送人",
    component: "Select",
    defaultValue: 0,
    componentProps: {
      placeholder: "请选择是否启用抄送人",
      options: [
        {
          label: "否",
          value: 0
        },
        {
          label: "是",
          value: 1
        }
      ]
    }
  }, {
    name: "enableApplyReason",
    label: "启用申请理由",
    component: "Select",
    defaultValue: 0,
    componentProps: {
      placeholder: "请选择是否启用申请理由",
      options: [
        {
          label: "否",
          value: 0
        },
        {
          label: "是",
          value: 1
        }
      ]
    }
  }, {
    name: "enableAttachment",
    label: "启用附件",
    component: "Select",
    defaultValue: 0,
    componentProps: {
      placeholder: "请选择是否启用附件",
      options: [
        {
          label: "否",
          value: 0
        },
        {
          label: "是",
          value: 1
        }
      ]
    }
  }]
}, Ts = {
  labelWidth: "130px",
  formItems: [{
    name: "name",
    label: "流程定义唯一编码",
    component: "Input",
    componentProps: {
      placeholder: "请输入流程定义唯一编码"
    }
  }, {
    name: "displayName",
    label: "流程定义显示名称",
    component: "Input",
    componentProps: {
      placeholder: "请输入流程定义显示名称"
    }
  }, {
    name: "form",
    label: "表单",
    component: "Input",
    componentProps: {
      placeholder: "请输入表单"
    }
  }, {
    name: "version",
    label: "版本号",
    component: "Input",
    componentProps: {
      placeholder: "请输入版本号"
    }
  }]
}, Ps = {
  labelWidth: "120px",
  formItems: [{
    name: "name",
    label: "唯一编码",
    component: "Input",
    componentProps: {
      placeholder: "请输入唯一编码"
    }
  }, {
    name: "expr",
    label: "决策表达式",
    component: "Input",
    componentProps: {
      placeholder: "请输入决策表达式"
    }
  }, {
    name: "handleClass",
    label: "处理类",
    component: "Input",
    componentProps: {
      placeholder: "请输入处理类"
    }
  }, {
    name: "clazz",
    label: "类路径",
    component: "Input",
    componentProps: {
      placeholder: "请输入类路径"
    }
  }, {
    name: "methodName",
    label: "方法名",
    component: "Input",
    componentProps: {
      placeholder: "请输入方法名"
    }
  }, {
    name: "args",
    label: "参数变量",
    component: "Input",
    componentProps: {
      placeholder: "请输入参数变量"
    }
  }, {
    name: "preInterceptors",
    label: "前置拦截器",
    component: "Input",
    componentProps: {
      placeholder: "请输入前置拦截器"
    }
  }, {
    name: "postInterceptors",
    label: "后置拦截器",
    component: "Input",
    componentProps: {
      placeholder: "请输入后置拦截器"
    }
  }]
}, Ms = {
  labelWidth: "120px",
  formItems: [{
    name: "name",
    label: "唯一编码",
    component: "Input",
    componentProps: {
      placeholder: "请输入唯一编码"
    }
  }, {
    name: "displayName",
    label: "显示名称",
    component: "Input",
    componentProps: {
      placeholder: "请输入显示名称"
    }
  }, {
    name: "clazz",
    label: "类路径",
    component: "Input",
    componentProps: {
      placeholder: "请输入类路径"
    }
  }, {
    name: "methodName",
    label: "方法名",
    component: "Input",
    componentProps: {
      placeholder: "请输入方法名"
    }
  }, {
    name: "args",
    label: "参数变量",
    component: "Input",
    componentProps: {
      placeholder: "请输入参数变量"
    }
  }, {
    name: "preInterceptors",
    label: "前置拦截器",
    component: "Input",
    componentProps: {
      placeholder: "请输入前置拦截器"
    }
  }, {
    name: "postInterceptors",
    label: "后置拦截器",
    component: "Input",
    componentProps: {
      placeholder: "请输入后置拦截器"
    }
  }]
}, Es = {
  key: 1,
  class: "ding-empty"
}, Ls = { class: "ding-modal__json" }, As = {
  key: 0,
  class: "ding-modal__error"
}, Ss = /* @__PURE__ */ q({
  __name: "DingTalkDesigner",
  props: {
    value: {
      type: Object,
      default: () => ({})
    },
    theme: {
      type: Object,
      default: () => ({})
    },
    highLight: {
      type: Object,
      default: () => ({})
    },
    viewer: {
      type: Boolean,
      default: !1
    },
    dndPanel: {
      type: Array,
      default: () => []
    },
    processForm: {
      type: Object
    },
    edgeForm: {
      type: Object
    },
    nodeClick: {
      type: Function
    },
    edgeClick: {
      type: Function
    },
    blankContextmenu: {
      type: Function
    },
    initControl: {
      type: Boolean,
      default: !0
    },
    control: {
      type: Array
    },
    drawerWidth: {
      type: [String, Number],
      default: "600px"
    },
    modalWidth: {
      type: [String, Number],
      default: "60%"
    },
    typePrefix: {
      type: String,
      default: "snaker:"
    },
    defaultEdgeType: {
      type: String,
      default: "snaker:transition"
    }
  },
  emits: ["update:value", "node-click", "edge-click", "edit-branch", "save", "on-init", "on-render"],
  setup(e, { expose: l, emit: i }) {
    const n = e, s = i, c = [
      { type: "task", text: "审批人", label: "审批人" },
      { type: "custom", text: "自定义节点", label: "自定义节点" },
      { type: "subProcess", text: "子流程", label: "子流程" }
    ], a = E(() => {
      const d = n.dndPanel || [], m = [...c];
      for (const k of d) {
        const I = m.findIndex((A) => {
          var se;
          return A.type === k.type || A.type === ((se = k.type) == null ? void 0 : se.replace(n.typePrefix, ""));
        });
        I >= 0 ? m[I] = { ...m[I], ...k } : m.push(k);
      }
      return m;
    }), r = b(void 0), y = E(() => {
      const d = /* @__PURE__ */ new Set();
      if (!r.value) return d;
      r.value.type.replace(n.typePrefix, "") === "start" && d.add(r.value.id);
      const k = r.value.children;
      k && d.add(k.id);
      const I = v(r.value);
      return I && d.add(I), d;
    });
    function v(d) {
      if (!d) return null;
      if (d.type.replace(n.typePrefix, "") === "end") return d.id;
      if (Ce(d)) {
        for (const k of d.branches)
          if (k.children) {
            const I = v(k.children);
            if (I) return I;
          }
      }
      if (Ie(d)) {
        for (const k of d.branches)
          if (k.children) {
            const I = v(k.children);
            if (I) return I;
          }
        if (d.joinChildren) {
          const k = v(d.joinChildren);
          if (k) return k;
        }
      }
      return "children" in d && d.children ? v(d.children) : null;
    }
    const h = b(null);
    let p = !1;
    const f = Ue({ scale: 1, x: 0, y: 0 }), j = b(!1), g = { x: 0, y: 0, originX: 0, originY: 0 }, C = b(null), D = b(!1), T = b(!1), N = {
      // 单指 pan
      x: 0,
      y: 0,
      originX: 0,
      originY: 0,
      // 双指 pinch
      distance: 0,
      centerX: 0,
      centerY: 0,
      originScale: 1
    }, U = E(() => {
      const d = n.control || [], k = [...[
        { key: "ding-zoom-out", iconClass: "ding-icon-zoom-out", title: "缩小流程图", text: "缩小", sort: 10, onClick: V },
        { key: "ding-zoom-in", iconClass: "ding-icon-zoom-in", title: "放大流程图", text: "放大", sort: 20, onClick: B },
        { key: "ding-fit", iconClass: "ding-icon-fit", title: "恢复初始位置和尺寸", text: "适应", sort: 30, onClick: S }
      ]];
      for (const I of d) {
        const A = k.findIndex((se) => se.key === I.key);
        A >= 0 ? k[A] = { ...k[A], ...I } : k.push(I);
      }
      return k.sort((I, A) => (I.sort || 0) - (A.sort || 0));
    }), P = E(() => ({
      transform: `translate(${f.x}px, ${f.y}px) scale(${f.scale})`,
      transformOrigin: "0 0"
    }));
    function B() {
      F(1.1);
    }
    function V() {
      F(1 / 1.1);
    }
    function F(d) {
      const m = Math.min(2, Math.max(0.3, f.scale * d)), k = C.value;
      if (k) {
        const I = k.getBoundingClientRect(), A = I.width / 2, se = I.height / 2;
        f.x = A - (A - f.x) * (m / f.scale), f.y = se - (se - f.y) * (m / f.scale);
      }
      f.scale = m;
    }
    function S() {
      f.scale = 1, f.x = 0, f.y = 0;
    }
    function z(d) {
      if (!(d.ctrlKey || d.metaKey)) return;
      d.preventDefault();
      const m = d.deltaY < 0 ? 1.1 : 1 / 1.1, k = C.value;
      if (k) {
        const I = k.getBoundingClientRect(), A = d.clientX - I.left, se = d.clientY - I.top, me = Math.min(2, Math.max(0.3, f.scale * m));
        f.x = A - (A - f.x) * (me / f.scale), f.y = se - (se - f.y) * (me / f.scale), f.scale = me;
      }
    }
    function W(d) {
      d.button !== 0 && d.button !== 1 || d.target.closest(".ding-node-card, button, .ding-edit-panel, .ding-modal, .ding-designer__zoom-controls, .ding-branch-col__head, .ding-condition-group__title, .ding-add-button") || pe(d);
    }
    function fe(d) {
      d.button !== 0 && d.button !== 1 || d.target.closest(".ding-node-card, button, .ding-edit-panel, .ding-modal, .ding-designer__zoom-controls, .ding-branch-col__head, .ding-condition-group__title, .ding-add-button") || pe(d);
    }
    function pe(d) {
      j.value = !0, g.x = d.clientX, g.y = d.clientY, g.originX = f.x, g.originY = f.y, document.addEventListener("mousemove", $), document.addEventListener("mouseup", _);
    }
    function $(d) {
      j.value && (f.x = g.originX + (d.clientX - g.x), f.y = g.originY + (d.clientY - g.y));
    }
    function _() {
      j.value = !1, document.removeEventListener("mousemove", $), document.removeEventListener("mouseup", _);
    }
    function x(d) {
      const m = d;
      return m ? !!m.closest(".ding-node-card, button, .ding-edit-panel, .ding-modal, .ding-designer__zoom-controls, .ding-branch-col__head, .ding-condition-group__title, .ding-add-button") : !1;
    }
    function L(d, m) {
      const k = d.clientX - m.clientX, I = d.clientY - m.clientY;
      return Math.hypot(k, I);
    }
    function ie(d, m) {
      return { x: (d.clientX + m.clientX) / 2, y: (d.clientY + m.clientY) / 2 };
    }
    function K(d) {
      if (!x(d.target)) {
        if (d.touches.length === 1) {
          const m = d.touches[0];
          D.value = !0, N.x = m.clientX, N.y = m.clientY, N.originX = f.x, N.originY = f.y;
        } else if (d.touches.length === 2) {
          const [m, k] = [d.touches[0], d.touches[1]];
          T.value = !0, D.value = !1, N.distance = L(m, k), N.originScale = f.scale;
          const I = ie(m, k);
          N.centerX = I.x, N.centerY = I.y;
        }
      }
    }
    function Q(d) {
      if (d.touches.length === 2 && T.value) {
        const [m, k] = [d.touches[0], d.touches[1]], I = L(m, k);
        if (N.distance > 0) {
          const A = I / N.distance, se = Math.min(2, Math.max(0.3, N.originScale * A)), me = C.value;
          if (me) {
            const tn = me.getBoundingClientRect(), nn = N.centerX - tn.left, ln = N.centerY - tn.top;
            f.x = nn - (nn - f.x) * (se / f.scale), f.y = ln - (ln - f.y) * (se / f.scale), f.scale = se;
          }
        }
        return;
      }
      if (d.touches.length === 1 && D.value) {
        const m = d.touches[0];
        f.x = N.originX + (m.clientX - N.x), f.y = N.originY + (m.clientY - N.y);
      }
    }
    function Z(d) {
      if (d.touches.length === 0)
        D.value = !1, T.value = !1;
      else if (d.touches.length === 1 && T.value) {
        const m = d.touches[0];
        T.value = !1, D.value = !0, N.x = m.clientX, N.y = m.clientY, N.originX = f.x, N.originY = f.y;
      }
    }
    We(() => {
      document.removeEventListener("mousemove", $), document.removeEventListener("mouseup", _);
    });
    function re(d, m) {
      if (Ce(d)) {
        if (d.branches.some((k) => k.id === m))
          return "condition";
        for (const k of d.branches)
          if (k.children) {
            const I = re(k.children, m);
            if (I) return I;
          }
      }
      if (Ie(d)) {
        if (d.branches.some((k) => k.id === m))
          return "fork";
        for (const k of d.branches)
          if (k.children) {
            const I = re(k.children, m);
            if (I) return I;
          }
      }
      return d.children ? re(d.children, m) : null;
    }
    let ye = !1;
    function oe() {
      var d, m;
      const k = ((d = n.value) == null ? void 0 : d.nodes) || [], I = ((m = n.value) == null ? void 0 : m.edges) || [], A = It(k, I, n.typePrefix);
      A ? r.value = A : !n.viewer && !ye && (ye = !0, we());
    }
    function we() {
      r.value = It(Ol, zl, n.typePrefix);
    }
    function ue() {
      const d = xt(r.value, n.typePrefix), m = {
        ...n.value,
        nodes: d.nodes,
        edges: d.edges,
        mode: "dingtalk"
      };
      p = !0, s("update:value", m), ve.emit("update:graphData", m);
    }
    const Ee = Ue({}), ve = {
      emit(d, m) {
        (Ee[d] || []).forEach((I) => I(m));
      },
      on(d, m) {
        Ee[d] || (Ee[d] = []), Ee[d].push(m);
      },
      off(d, m) {
        const k = Ee[d] || [], I = k.indexOf(m);
        I >= 0 && k.splice(I, 1);
      }
    };
    oe();
    function Ge(d) {
      const m = n.typePrefix;
      return d === "condition" ? `${m}decision` : d === "fork" ? `${m}fork` : d === "join" ? `${m}join` : d.startsWith(m) ? d : `${m}${d}`;
    }
    function De(d) {
      return {
        id: d.id,
        type: Ge(d.type),
        text: { value: d.name },
        properties: d.properties || {}
      };
    }
    function ze(d) {
      return Be(
        r.value,
        (m) => {
          var k;
          return m.id === d || ((k = m.properties) == null ? void 0 : k.name) === d;
        }
      );
    }
    function Ze(d, m) {
      if (!r.value) return null;
      const k = ze(d);
      return k || Be(r.value, (I) => {
        var A;
        return ((A = I.properties) == null ? void 0 : A.name) === d;
      });
    }
    const Re = {
      // ── 查询 ──
      getNodeDataById(d) {
        if (n.viewer) return null;
        const m = Be(r.value, (k) => k.id === d);
        return m ? De(m) : null;
      },
      getNodeDataByName(d) {
        if (n.viewer) return null;
        const m = Be(r.value, (k) => {
          var I;
          return ((I = k.properties) == null ? void 0 : I.name) === d;
        });
        return m ? De(m) : null;
      },
      getAllNodes() {
        return ct(r.value).map(De);
      },
      getProperties(d) {
        const m = Ze(d);
        return m ? { ...m.properties } : {};
      },
      // ── 更新 ──
      updateText(d, m) {
        const k = Ze(d);
        k && (k.name = m), ue();
      },
      changeNodeId(d, m) {
        if (n.viewer) return !1;
        const k = Be(r.value, (I) => I.id === d);
        return k ? (k.id = m, k.properties = { ...k.properties, name: m }, ue(), !0) : !1;
      },
      setProperties(d, m) {
        if (m.viewer) return;
        const k = Ze(d);
        k && (k.properties = { ...k.properties, ...m }), ue();
      },
      deleteProperty(d, m) {
        if (n.viewer) return;
        const k = Ze(d);
        if (k && k.properties && m in k.properties) {
          const I = { ...k.properties };
          delete I[m], k.properties = I;
        }
        ue();
      },
      // ── 流程属性（v-model.value） ──
      setProcessProperty(d, m) {
        if (n.viewer) return;
        const k = { ...n.value, [d]: m };
        p = !0, s("update:value", k), ve.emit("update:graphModel", k);
      },
      // ── 导出/重渲染 ──
      getGraphData() {
        const d = xt(r.value, n.typePrefix);
        return {
          ...n.value,
          nodes: d.nodes,
          edges: d.edges,
          mode: "dingtalk"
        };
      },
      render(d) {
        p = !0, r.value = It((d == null ? void 0 : d.nodes) || [], (d == null ? void 0 : d.edges) || [], n.typePrefix), p = !1, ue(), ve.emit("update:graphData", d);
      },
      // ── 高亮 ──
      setHighlight(d) {
        ve.emit("update:highlight", d);
      },
      // ── 事件总线 ──
      eventCenter: ve,
      // ── graphModel 代理（与画布模式 lf.graphModel 兼容） ──
      // 业务方 vben5 process-drawer.vue 的写法：
      //   lfInstance.graphModel[key] = value
      //   lfInstance.graphModel.eventCenter.emit('update:graphModel', graphModel)
      // 在钉钉模式无需任何修改也能跑通
      graphModel: At()
    };
    let Fe = {};
    be(() => n.value, () => {
      p || (Fe = {});
    });
    function At() {
      return new Proxy({}, {
        get(d, m) {
          var k;
          return m === "eventCenter" ? ve : m in Fe ? Fe[m] : (k = n.value) == null ? void 0 : k[m];
        },
        set(d, m, k) {
          if (n.viewer) return !0;
          Fe[m] = k;
          const I = { ...n.value, ...Fe };
          return p = !0, s("update:value", I), ve.emit("update:graphModel", I), !0;
        },
        has(d, m) {
          return m === "eventCenter" || m in Fe || m in (n.value || {});
        }
      });
    }
    l(Re), he(() => {
      s("on-init", Re), s("on-render", Re);
    }), be(() => n.value, () => {
      if (p) {
        p = !1;
        return;
      }
      oe();
    }, { deep: !0 });
    const Y = E(() => {
      var d, m, k, I;
      const A = {};
      return (d = n.theme) != null && d.backgroundColor && (A["--ding-bg-color"] = n.theme.backgroundColor), (m = n.theme) != null && m.primaryColor && (A["--ding-primary-color"] = n.theme.primaryColor), (k = n.theme) != null && k.activeColor && (A["--ding-active-color"] = n.theme.activeColor), (I = n.theme) != null && I.historyColor && (A["--ding-history-color"] = n.theme.historyColor), A;
    });
    let R = 0;
    function O() {
      return typeof crypto < "u" && typeof crypto.randomUUID == "function" ? `ding_${crypto.randomUUID()}` : `ding_${Date.now()}_${++R}`;
    }
    function ge(d) {
      return !d || d.startsWith(n.typePrefix) ? d : `${n.typePrefix}${d}`;
    }
    function Le(d, m) {
      if (!r.value) return;
      if (d === "__condition__") {
        An(m), ue();
        return;
      }
      if (d === "__parallel__") {
        Sn(m), ue();
        return;
      }
      const k = ge(d), I = {
        id: O(),
        type: k,
        name: He(k),
        properties: {}
      };
      m && et(r.value, m.id, I), ue();
    }
    function bt(d) {
      return r.value ? !(y.value.has(d.id) || Zt(r.value, d.id)) : !0;
    }
    function kt(d) {
      if (!r.value) return;
      const m = d.type.replace(n.typePrefix, "");
      if (y.value.has(d.id)) {
        console.warn("[DingTalkDesigner] 受保护节点不允许删除：", d.id);
        return;
      }
      if (!(m === "start" || m === "end")) {
        if (Zt(r.value, d.id)) {
          console.warn("[DingTalkDesigner] 并行分支只有 2 条，不允许删除会让分支变空的任务：", d.id);
          return;
        }
        Ce(d) ? it(r.value, d.id) : Ie(d) ? jt(r.value, d.id) : ot(r.value, d.id), Ln(r.value), ue();
      }
    }
    function Zt(d, m) {
      function k(I) {
        if (Ce(I)) {
          const A = I;
          for (const se of A.branches)
            if (se.children && k(se.children)) return !0;
        }
        if (Ie(I)) {
          const A = I;
          if (A.branches.length === 2) {
            for (const se of A.branches)
              if (se.children && se.children.id === m && !se.children.children)
                return !0;
          }
          for (const se of A.branches)
            if (se.children && k(se.children)) return !0;
          if (A.joinChildren && k(A.joinChildren)) return !0;
        }
        return I.children ? k(I.children) : !1;
      }
      return k(d);
    }
    function Tn(d) {
      var m, k;
      if (n.viewer) return;
      const I = d.type.replace(n.typePrefix, ""), A = a.value.find(
        (me) => me.type === I || me.type === d.type
      ), se = {
        data: De(d),
        node: d,
        patternItem: A,
        lf: Re
      };
      if (A != null && A.nodeClick && typeof A.nodeClick == "function") {
        A.nodeClick(se);
        return;
      }
      if (n.nodeClick && typeof n.nodeClick == "function") {
        n.nodeClick(se);
        return;
      }
      Ae.value = null, Ne.value = d, en.value = A == null ? void 0 : A.form, _e.name = ((m = d.properties) == null ? void 0 : m.name) || d.id, _e.displayName = d.name || "";
      for (const me of St.value)
        me.name === "name" || me.name === "displayName" || (_e[me.name] = ((k = d.properties) == null ? void 0 : k[me.name]) ?? me.defaultValue ?? "");
      s("node-click", se);
    }
    function Pn(d) {
      var m, k;
      if (n.viewer) return;
      const I = {
        data: {
          id: d.id,
          type: "transition",
          text: { value: d.name },
          properties: d.properties || {}
        },
        edge: d,
        patternItem: { form: n.edgeForm },
        lf: Re
      };
      if (n.edgeClick && typeof n.edgeClick == "function") {
        n.edgeClick(I);
        return;
      }
      Ne.value = null, Ae.value = d, h.value = r.value ? re(r.value, d.id) : null, _e.displayName = d.name || "", _e.expr = ((m = d.properties) == null ? void 0 : m.expr) || "", _e.name = ((k = d.properties) == null ? void 0 : k.name) || d.id, s("edge-click", I);
    }
    function Mn(d) {
      const m = ge("task"), k = {
        id: O(),
        type: m,
        name: He(m),
        properties: {}
      };
      if (Ce(d)) {
        const I = d, A = {
          id: O(),
          name: `条件${I.branches.length + 1}`,
          properties: {},
          children: k
        };
        I.branches.push(A), ue();
        return;
      }
      if (Ie(d)) {
        const I = d, A = {
          id: O(),
          name: `分支${I.branches.length + 1}`,
          properties: {},
          children: k
        };
        I.branches.push(A), ue();
      }
    }
    function En(d, m) {
      if (!r.value) return;
      if (d === "__condition__") {
        const A = {
          id: O(),
          type: "condition",
          name: "",
          properties: {},
          branches: [
            { id: O(), name: "条件1", properties: {} },
            { id: O(), name: "条件2", properties: {} }
          ]
        };
        m.children = A, ue();
        return;
      }
      const k = ge(d), I = {
        id: O(),
        type: k,
        name: He(k),
        properties: {}
      };
      m.children = I, ue();
    }
    function et(d, m, k) {
      if (d.id === m)
        return k.children = d.children, d.children = k, !0;
      if (Ce(d)) {
        const I = d;
        for (const A of I.branches)
          if (A.children && et(A.children, m, k))
            return !0;
      }
      if (Ie(d)) {
        const I = d;
        for (const A of I.branches)
          if (A.children && et(A.children, m, k))
            return !0;
        if (I.joinChildren && et(I.joinChildren, m, k))
          return !0;
      }
      return d.children ? et(d.children, m, k) : !1;
    }
    function ot(d, m) {
      if (d.children && d.children.id === m) {
        const k = d.children;
        return d.children = k.children, !0;
      }
      if (Ce(d)) {
        const k = d;
        for (const I of k.branches)
          if (I.children) {
            if (I.children.id === m) {
              const A = I.children;
              return I.children = A.children, !0;
            }
            if (ot(I.children, m))
              return !0;
          }
      }
      if (Ie(d)) {
        const k = d;
        for (const I of k.branches)
          if (I.children) {
            if (I.children.id === m)
              return I.children = I.children.children, !0;
            if (ot(I.children, m))
              return !0;
          }
        if (k.joinChildren) {
          if (k.joinChildren.id === m)
            return k.joinChildren = k.joinChildren.children || void 0, !0;
          if (ot(k.joinChildren, m))
            return !0;
        }
      }
      return d.children ? ot(d.children, m) : !1;
    }
    function Ln(d) {
      if (!d) return;
      function m(k) {
        if (Ce(k)) {
          const I = k;
          I.branches.length > 2 && (I.branches = I.branches.filter((A) => A.children !== void 0));
          for (const A of I.branches)
            A.children && m(A.children);
        } else if (Ie(k)) {
          const I = k;
          I.branches.length > 2 && (I.branches = I.branches.filter((A) => A.children !== void 0));
          for (const A of I.branches)
            A.children && m(A.children);
          I.joinChildren && m(I.joinChildren);
        } else k.children && m(k.children);
      }
      m(d);
    }
    function it(d, m) {
      if (d.children && d.children.id === m && Ce(d.children))
        return d.children = d.children.children, !0;
      if (Ce(d)) {
        const k = d;
        for (const I of k.branches) {
          if (I.children && I.children.id === m && Ce(I.children))
            return I.children = I.children.children, !0;
          if (I.children && it(I.children, m))
            return !0;
        }
      }
      if (Ie(d)) {
        const k = d;
        for (const I of k.branches)
          if (I.children && it(I.children, m))
            return !0;
        if (k.joinChildren && it(k.joinChildren, m))
          return !0;
      }
      return d.children ? it(d.children, m) : !1;
    }
    function jt(d, m) {
      var k;
      if (d.children && d.children.id === m && Ie(d.children))
        return d.children = (k = d.children.joinChildren) == null ? void 0 : k.children, !0;
      if (Ie(d)) {
        const I = d;
        for (const A of I.branches)
          if (A.children && jt(A.children, m))
            return !0;
        if (I.joinChildren && jt(I.joinChildren, m))
          return !0;
      }
      return d.children ? jt(d.children, m) : !1;
    }
    function An(d) {
      if (!r.value || !d) return;
      const m = ge("task"), k = {
        id: O(),
        type: m,
        name: He(m),
        properties: {}
      }, I = {
        id: O(),
        type: m,
        name: He(m),
        properties: {}
      }, A = {
        id: O(),
        type: "condition",
        name: "",
        properties: {},
        branches: [
          { id: O(), name: "条件1", properties: {}, children: k },
          { id: O(), name: "条件2", properties: {}, children: I }
        ]
      };
      et(r.value, d.id, A);
    }
    function Sn(d) {
      if (!r.value || !d) return;
      const m = O(), k = {
        id: m,
        type: ge("join"),
        name: "合并节点",
        properties: {},
        children: d.children
        // 接管原 afterNode.children
      }, I = ge("task"), A = {
        id: O(),
        type: I,
        name: He(I),
        properties: {}
      }, se = {
        id: O(),
        type: I,
        name: He(I),
        properties: {}
      }, me = {
        id: O(),
        type: "fork",
        name: "",
        properties: {},
        branches: [
          { id: O(), name: "分支1", properties: {}, children: A },
          { id: O(), name: "分支2", properties: {}, children: se }
        ],
        joinId: m,
        joinChildren: k
      };
      d.children = me;
    }
    function He(d) {
      switch (d.replace(n.typePrefix, "")) {
        case "task":
          return "审批人";
        case "custom":
          return "自定义节点";
        case "subProcess":
          return "子流程";
        default:
          return "新节点";
      }
    }
    const Ne = b(null), Ae = b(null), On = E(() => !!Ne.value || !!Ae.value), _e = Ue({
      name: "",
      displayName: "",
      assignee: "",
      assignmentHandler: "",
      candidateUsers: "",
      candidateGroups: "",
      candidateHandler: "",
      taskType: "",
      performType: "",
      countersignType: "",
      countersignCompletionCondition: "",
      actionBtns: "",
      callback: "",
      reminderTime: "",
      reminderRepeat: "",
      expireTime: "",
      autoExecute: "",
      clazz: "",
      methodName: "",
      args: "",
      form: "",
      version: "",
      preInterceptors: "",
      postInterceptors: "",
      expr: "",
      handleClass: ""
    }), zn = E(() => {
      if (Ae.value) return "编辑分支条件";
      if (!Ne.value) return "";
      switch (Ne.value.type.replace(n.typePrefix, "")) {
        case "start":
          return "编辑开始节点";
        case "end":
          return "编辑结束节点";
        case "task":
          return "编辑审批节点";
        case "custom":
          return "编辑自定义节点";
        case "subProcess":
          return "编辑子流程";
        case "condition":
          return "编辑条件分支（决策配置）";
        case "fork":
          return "编辑并行分支";
        default:
          return "编辑节点";
      }
    }), Bn = {
      task: Ns,
      condition: Ps,
      custom: Ms,
      subProcess: Ts,
      start: xs,
      end: Ds
    }, en = b(void 0), St = E(() => {
      if (Ae.value) {
        const A = [
          { name: "displayName", label: "分支名称", component: "Input", componentProps: { placeholder: "请输入分支名称" } }
        ];
        return h.value === "condition" && A.push({ name: "expr", label: "条件表达式", component: "Input", componentProps: { placeholder: "请输入条件表达式" } }), A;
      }
      if (!Ne.value) return [];
      const d = Ne.value.type.replace(n.typePrefix, ""), m = [
        { name: "name", label: "唯一编码", component: "Input", componentProps: { placeholder: "请输入唯一编码" } },
        { name: "displayName", label: "显示名称", component: "Input", componentProps: { placeholder: "请输入显示名称" } }
      ], k = en.value || Bn[d];
      if (!(k != null && k.formItems)) return m;
      let I = k.formItems.filter((A) => A.name !== "__schema__");
      if (!I.some((A) => A.name === "displayName") && d !== "start" && d !== "end") {
        const A = I.findIndex((me) => me.name === "name"), se = { name: "displayName", label: "显示名称", component: "Input", componentProps: { placeholder: "请输入显示名称" } };
        I = [...I.slice(0, A + 1), se, ...I.slice(A + 1)];
      }
      return I;
    });
    function Un() {
      Ne.value = null, Ae.value = null;
    }
    function Vn() {
      if (Ae.value) {
        Ae.value.name = _e.displayName, Ae.value.properties = {
          ...Ae.value.properties,
          expr: _e.expr,
          name: _e.name
        };
        return;
      }
      if (Ne.value) {
        const d = St.value;
        d.some((k) => k.name === "displayName") && (Ne.value.name = _e.displayName);
        const m = {
          ...Ne.value.properties,
          name: _e.name
        };
        for (const k of d)
          k.name === "name" || k.name === "displayName" || (m[k.name] = _e[k.name]);
        Ne.value.properties = m;
      }
    }
    be(
      _e,
      () => {
        (Ne.value || Ae.value) && Vn();
      },
      { deep: !0 }
    );
    function Rn(d) {
      if (n.viewer) return;
      const m = n.processForm || fn, k = {};
      if (m != null && m.formItems)
        for (const A of m.formItems)
          n.value && Object.prototype.hasOwnProperty.call(n.value, A.name) && (k[A.name] = n.value[A.name]);
      const I = {
        data: {
          type: "process",
          properties: k
        },
        patternItem: { form: m },
        lf: Re
      };
      if (n.blankContextmenu && typeof n.blankContextmenu == "function") {
        n.blankContextmenu(I);
        return;
      }
      Ot.value.length > 0 && Jn();
    }
    const $t = b(!1), wt = b(""), Fn = E(() => {
      try {
        return JSON.parse(wt.value || "{}");
      } catch {
        return {};
      }
    }), rt = b(!1), _t = b(""), Je = b(""), Ct = b(!1), dt = Ue({}), Ot = E(() => {
      var d;
      const m = (d = n.processForm || fn) == null ? void 0 : d.formItems;
      return m ? m.filter((k) => k.name !== "__schema__") : [];
    });
    function Jn() {
      Ot.value.forEach((d) => {
        var m;
        dt[d.name] = ((m = n.value) == null ? void 0 : m[d.name]) ?? d.defaultValue ?? "";
      }), Ct.value = !0;
    }
    function Yn() {
      Ct.value = !1;
      const d = { ...n.value, ...dt };
      p = !0, s("update:value", d), ve.emit("update:graphModel", d);
    }
    be(
      dt,
      () => {
        if (!Ct.value) return;
        const d = { ...n.value, ...dt };
        p = !0, s("update:value", d), ve.emit("update:graphModel", d);
      },
      { deep: !0 }
    );
    function Wn() {
      const d = xt(r.value, n.typePrefix), m = {
        ...n.value,
        nodes: d.nodes,
        edges: d.edges,
        mode: "dingtalk"
      };
      s("save", m);
    }
    function Gn() {
      const d = {
        id: O(),
        type: `${n.typePrefix}start`,
        name: "开始",
        properties: {},
        children: {
          id: O(),
          type: `${n.typePrefix}task`,
          name: "申请",
          properties: {},
          children: {
            id: O(),
            type: `${n.typePrefix}end`,
            name: "结束",
            properties: {}
          }
        }
      };
      r.value = d, ue();
    }
    function Hn() {
      const d = xt(r.value, n.typePrefix), m = {
        ...n.value,
        nodes: d.nodes,
        edges: d.edges,
        mode: "dingtalk"
      };
      wt.value = JSON.stringify(m, null, 2), $t.value = !0;
    }
    function Kn() {
      _t.value = "", rt.value = !0;
    }
    function Qn() {
      Je.value = "";
      const d = JSON.stringify(r.value);
      try {
        const m = JSON.parse(_t.value);
        if (!m || typeof m != "object") {
          Je.value = "导入失败：数据格式不正确";
          return;
        }
        if (!Array.isArray(m.nodes) || !Array.isArray(m.edges)) {
          Je.value = "导入失败：缺少 nodes 或 edges 数组";
          return;
        }
        for (const I of m.nodes)
          if (!I || typeof I.id != "string" || typeof I.type != "string") {
            Je.value = "导入失败：节点缺少 id 或 type 字段";
            return;
          }
        for (const I of m.edges)
          if (!I || typeof I.id != "string" || typeof I.sourceNodeId != "string" || typeof I.targetNodeId != "string") {
            Je.value = "导入失败：边缺少 id / sourceNodeId / targetNodeId 字段";
            return;
          }
        p = !0;
        const k = {
          ...n.value,
          nodes: m.nodes,
          edges: m.edges,
          mode: m.mode === "canvas" ? "canvas" : "dingtalk"
        };
        s("update:value", k), r.value = It(k.nodes || [], k.edges || [], n.typePrefix), rt.value = !1;
      } catch {
        Je.value = "导入失败：JSON 格式不正确";
        try {
          r.value = JSON.parse(d);
        } catch {
        }
      }
    }
    function Xn() {
      var d;
      try {
        if ((d = navigator.clipboard) != null && d.writeText && window.isSecureContext)
          navigator.clipboard.writeText(wt.value);
        else {
          const m = document.createElement("textarea");
          m.value = wt.value, document.body.appendChild(m), m.select(), document.execCommand("copy"), document.body.removeChild(m);
        }
        cn.success("复制成功");
      } catch (m) {
        cn.error(`复制失败: ${m instanceof Error ? m.message : String(m)}`);
      }
    }
    function qn() {
      var d, m;
      const k = document.querySelector(".ding-designer");
      k && (document.fullscreenElement ? (m = document.exitFullscreen) == null || m.call(document).catch(() => {
      }) : (d = k.requestFullscreen) == null || d.call(k).catch(() => {
      }));
    }
    return (d, m) => (o(), u("div", {
      class: "ding-designer",
      style: ce(Y.value),
      onContextmenu: Se(Rn, ["prevent"])
    }, [
      J(Is, {
        "init-control": e.initControl,
        control: U.value,
        viewer: e.viewer,
        onSave: Wn,
        onClear: Gn,
        onViewData: Hn,
        onImportData: Kn,
        onFullscreen: qn
      }, null, 8, ["init-control", "control", "viewer"]),
      t("div", {
        class: ne(["ding-designer__canvas", { "is-dragging": j.value, "is-touch-dragging": D.value, "is-pinching": T.value }]),
        ref_key: "canvasRef",
        ref: C,
        onWheel: z,
        onMousedown: W,
        onTouchstartPassive: K,
        onTouchmovePassive: Q,
        onTouchendPassive: Z,
        onTouchcancelPassive: Z
      }, [
        t("div", {
          class: "ding-designer__viewport",
          style: ce(P.value),
          onMousedown: fe
        }, [
          r.value ? (o(), ae(Tt, {
            key: 0,
            node: r.value,
            "type-prefix": e.typePrefix,
            viewer: e.viewer,
            "high-light": e.highLight,
            theme: e.theme,
            "dnd-panel": a.value,
            "protected-ids": y.value,
            "can-delete-checker": bt,
            onEdit: Tn,
            onDelete: kt,
            onAdd: Le,
            onAddBranch: Mn,
            onEditBranch: Pn,
            onAddToBranch: En
          }, null, 8, ["node", "type-prefix", "viewer", "high-light", "theme", "dnd-panel", "protected-ids"])) : (o(), u("div", Es, [...m[5] || (m[5] = [
            t("div", { class: "ding-empty__title" }, "暂无流程数据", -1)
          ])]))
        ], 36)
      ], 34),
      J(H(sn), {
        visible: On.value,
        title: zn.value,
        width: "600px",
        "show-footer": !1,
        onCancel: Un
      }, {
        default: te(() => [
          J(H(rn), {
            "form-items": St.value,
            model: _e,
            "label-width": "120px"
          }, null, 8, ["form-items", "model"])
        ]),
        _: 1
      }, 8, ["visible", "title"]),
      J(H(on), {
        visible: $t.value,
        "onUpdate:visible": m[0] || (m[0] = (k) => $t.value = k),
        title: "流程数据",
        "cancel-text": "关闭",
        "ok-text": "复制",
        onOk: Xn,
        onCancel: m[1] || (m[1] = (k) => $t.value = !1),
        width: "600px"
      }, {
        default: te(() => [
          t("div", Ls, [
            J(H(Ma), {
              showLineNumber: !0,
              data: Fn.value
            }, null, 8, ["data"])
          ])
        ]),
        _: 1
      }, 8, ["visible"]),
      J(H(on), {
        visible: rt.value,
        "onUpdate:visible": m[3] || (m[3] = (k) => rt.value = k),
        title: "导入流程数据",
        onOk: Qn,
        onCancel: m[4] || (m[4] = (k) => rt.value = !1),
        width: "600px"
      }, {
        default: te(() => [
          J(H(Jl), {
            class: "ding-modal__textarea",
            modelValue: _t.value,
            "onUpdate:modelValue": m[2] || (m[2] = (k) => _t.value = k),
            placeholder: "请粘贴 JSON 数据"
          }, null, 8, ["modelValue"]),
          Je.value ? (o(), u("div", As, w(Je.value), 1)) : M("", !0)
        ]),
        _: 1
      }, 8, ["visible"]),
      J(H(sn), {
        visible: Ct.value,
        title: "流程属性",
        width: "600px",
        "show-footer": !1,
        onCancel: Yn
      }, {
        default: te(() => [
          J(H(rn), {
            "form-items": Ot.value,
            model: dt,
            "label-width": "130px"
          }, null, 8, ["form-items", "model"])
        ]),
        _: 1
      }, 8, ["visible"])
    ], 36));
  }
}), Os = { class: "flow-container" }, zs = /* @__PURE__ */ q({
  __name: "index.dingtalk",
  props: Tl,
  emits: ["update:value", "on-init", "on-render", "on-save", "node-click", "edge-click"],
  setup(e, { expose: l, emit: i }) {
    const n = i, s = b();
    return l({
      /**
       * 兼容双模式包的同名方法：返回 FDDesignerAPI
       * （其命名与画布模式 lf 实例对齐，业务方可按同一套代码消费）
       */
      getLfInstance() {
        return s.value;
      },
      getDesignerApi() {
        return s.value;
      }
    }), (c, a) => (o(), u("div", Os, [
      J(Ss, {
        ref_key: "dingtalkDesignerRef",
        ref: s,
        value: c.value,
        theme: c.theme,
        "high-light": c.highLight,
        viewer: c.viewer,
        "dnd-panel": c.dndPanel,
        "process-form": c.processForm,
        "edge-form": c.edgeForm,
        "node-click": c.nodeClick,
        "edge-click": c.edgeClick,
        "blank-contextmenu": c.blankContextmenu,
        control: c.control,
        "init-control": c.initControl,
        "drawer-width": c.drawerWidth,
        "modal-width": c.modalWidth,
        "type-prefix": c.typePrefix,
        "default-edge-type": c.defaultEdgeType,
        "onUpdate:value": a[0] || (a[0] = (r) => n("update:value", r)),
        onSave: a[1] || (a[1] = (r) => n("on-save", r)),
        onOnInit: a[2] || (a[2] = (r) => n("on-init", r)),
        onOnRender: a[3] || (a[3] = (r) => n("on-render", r)),
        onNodeClick: a[4] || (a[4] = (r) => n("node-click", r)),
        onEdgeClick: a[5] || (a[5] = (r) => n("edge-click", r))
      }, null, 8, ["value", "theme", "high-light", "viewer", "dnd-panel", "process-form", "edge-form", "node-click", "edge-click", "blank-contextmenu", "control", "init-control", "drawer-width", "modal-width", "type-prefix", "default-edge-type"])
    ]));
  }
}), Bs = /* @__PURE__ */ Me(zs, [["__scopeId", "data-v-6ea9cac0"]]), Pt = Bs;
Pt.install = function(e, l) {
  e.component("MldongFlowDesignerPlus", Pt);
};
const Us = {
  class: "jf-flow-viewer",
  ref: "container"
}, Vs = {
  key: 0,
  class: "jf-viewer-loading"
}, Rs = {
  key: 2,
  class: "jf-viewer-empty"
}, Fs = {
  key: 3,
  class: "jf-viewer-legend"
}, Js = /* @__PURE__ */ q({
  name: "JfFlowViewer",
  __name: "JfFlowViewer",
  props: {
    graphData: {},
    highLight: {},
    assigneeTextData: { default: () => [] },
    height: { default: "100%" },
    primaryColor: { default: "#1677ff" }
  },
  setup(e) {
    tl((v) => ({
      v19c9ef23: v.height
    }));
    const l = e, i = b(null);
    function n() {
      var h, p;
      const v = l.assigneeTextData;
      if (!(!(v != null && v.length) || !i.value))
        for (const f of v)
          f != null && f.value && (f != null && f.label) && ((p = (h = i.value).updateText) == null || p.call(h, f.value, f.label));
    }
    function s(v) {
      i.value = v, n();
    }
    be(() => l.assigneeTextData, n, { deep: !0 });
    const c = b(!1), a = E(() => l.graphData), r = E(
      () => {
        var v, h, p, f;
        return !!((h = (v = l.highLight) == null ? void 0 : v.activeNodeNames) != null && h.length || (f = (p = l.highLight) == null ? void 0 : p.historyNodeNames) != null && f.length);
      }
    ), y = E(() => ({
      primaryColor: l.primaryColor,
      edgePrimaryColor: l.primaryColor,
      activeColor: "#fa8c16",
      historyColor: "#52c41a",
      backgroundColor: "#fafbfc"
    }));
    return he(() => {
      setTimeout(() => c.value = !0, 100);
    }), (v, h) => (o(), u("div", Us, [
      c.value ? M("", !0) : (o(), u("div", Vs, "加载设计器...")),
      c.value && a.value ? (o(), ae(H(Pt), {
        key: 1,
        value: a.value,
        mode: "dingtalk",
        viewer: !0,
        "high-light": e.highLight ?? void 0,
        "assignee-text-data": e.assigneeTextData,
        theme: y.value,
        onOnInit: s
      }, null, 8, ["value", "high-light", "assignee-text-data", "theme"])) : c.value && !a.value ? (o(), u("div", Rs, "无流程图数据")) : M("", !0),
      r.value ? (o(), u("div", Fs, [...h[0] || (h[0] = [
        nl('<span class="lg" data-v-730e6a9c><i class="lg-dot lg-active" data-v-730e6a9c></i>进行中</span><span class="lg" data-v-730e6a9c><i class="lg-dot lg-history" data-v-730e6a9c></i>已完成</span><span class="lg" data-v-730e6a9c><i class="lg-dot lg-idle" data-v-730e6a9c></i>未激活</span>', 3)
      ])])) : M("", !0)
    ], 512));
  }
}), Lt = /* @__PURE__ */ $e(Js, [["__scopeId", "data-v-730e6a9c"]]), Ys = { class: "jup" }, Ws = ["onClick"], Gs = ["placeholder", "disabled"], Hs = {
  key: 0,
  class: "jup-tip"
}, Ks = {
  key: 1,
  class: "jup-tip"
}, Qs = {
  key: 2,
  class: "jup-tip"
}, Xs = ["onClick"], qs = { class: "jup-item-avatar" }, Zs = { class: "jup-item-main" }, eo = { class: "jup-item-name" }, to = {
  key: 0,
  class: "jup-item-sub"
}, no = /* @__PURE__ */ q({
  name: "JfUserPicker",
  __name: "JfUserPicker",
  props: {
    modelValue: { default: () => [] },
    taskId: { default: null },
    scene: {},
    apiHint: { default: "" },
    placeholder: { default: "输入姓名/工号搜索" },
    disabled: { type: Boolean, default: !1 }
  },
  emits: ["update:modelValue", "change"],
  setup(e, { emit: l }) {
    const i = e, n = l, { api: s, adapters: c } = je(), a = b(null), r = b(""), y = b(!1), v = b(!1), h = b(""), p = b([]), f = Ue({});
    let j = null;
    function g(F) {
      return f[F] || F;
    }
    function C() {
      var F;
      i.disabled || (F = a.value) == null || F.focus();
    }
    function D() {
      y.value = !0, P();
    }
    function T() {
      y.value = !1, r.value = "";
    }
    function N() {
      j && clearTimeout(j), j = setTimeout(P, 300);
    }
    const U = E(
      () => i.scene || (i.taskId ? "candidate" : "cc")
    );
    be(() => i.modelValue.slice(), async (F) => {
      const S = F.filter((z) => z && !f[z]);
      if (!(!S.length || !c.getUsersByIds))
        try {
          const z = await c.getUsersByIds(S);
          for (const W of z) W != null && W.userId && (W != null && W.realName) && (f[W.userId] = W.realName);
        } catch {
        }
    }, { immediate: !0 });
    async function P() {
      v.value = !0, h.value = "";
      try {
        const F = r.value.trim();
        let S = [];
        !!i.taskId && U.value === "candidate" ? S = (await s.processTask.candidatePage(i.taskId, {
          ...F ? { m_LIKE_realName: F } : {},
          pageNum: 1,
          pageSize: 10
        })).rows : c.listUsers ? S = await c.listUsers(F, {
          scene: U.value,
          taskId: i.taskId,
          apiHint: i.apiHint || void 0
        }) : h.value = "无用户源：请在 provider.adapters 注入 listUsers";
        for (const W of S) W != null && W.realName && (f[W.userId] = W.realName);
        p.value = S.filter((W) => !i.modelValue.includes(W.userId));
      } catch (F) {
        h.value = F.message || "用户搜索失败", p.value = [];
      } finally {
        v.value = !1;
      }
    }
    function B(F) {
      var z;
      const S = [...i.modelValue, F.userId];
      n("update:modelValue", S), n("change", S), r.value = "", p.value = p.value.filter((W) => W.userId !== F.userId), (z = a.value) == null || z.focus();
    }
    function V(F) {
      const S = i.modelValue.filter((z) => z !== F);
      n("update:modelValue", S), n("change", S);
    }
    return (F, S) => (o(), u("div", Ys, [
      t("div", {
        class: ne(["jup-box", { "jup-box--focus": y.value }]),
        onClick: C
      }, [
        (o(!0), u(G, null, le(e.modelValue, (z) => (o(), u("span", {
          key: z,
          class: "jup-chip"
        }, [
          ee(w(g(z)) + " ", 1),
          e.disabled ? M("", !0) : (o(), u("i", {
            key: 0,
            class: "jup-chip-x",
            onClick: Se((W) => V(z), ["stop"])
          }, "×", 8, Ws))
        ]))), 128)),
        de(t("input", {
          ref_key: "inputEl",
          ref: a,
          "onUpdate:modelValue": S[0] || (S[0] = (z) => r.value = z),
          class: "jup-input",
          placeholder: e.modelValue.length ? "" : e.placeholder,
          disabled: e.disabled,
          onFocus: D,
          onBlur: T,
          onInput: N
        }, null, 40, Gs), [
          [Te, r.value]
        ])
      ], 2),
      y.value ? (o(), u("div", {
        key: 0,
        class: "jup-pop",
        onMousedown: S[1] || (S[1] = Se(() => {
        }, ["prevent"]))
      }, [
        v.value ? (o(), u("div", Hs, "搜索中...")) : h.value ? (o(), u("div", Ks, w(h.value), 1)) : p.value.length ? (o(!0), u(G, { key: 3 }, le(p.value, (z) => (o(), u("div", {
          key: z.userId,
          class: "jup-item",
          onClick: (W) => B(z)
        }, [
          t("span", qs, w((z.realName || z.userId || "?").slice(0, 1)), 1),
          t("span", Zs, [
            t("span", eo, w(z.realName || z.userId), 1),
            z.deptName || z.postName ? (o(), u("span", to, w([z.deptName, z.postName].filter(Boolean).join(" · ")), 1)) : M("", !0)
          ])
        ], 8, Xs))), 128)) : (o(), u("div", Qs, "无匹配用户"))
      ], 32)) : M("", !0)
    ]));
  }
}), at = /* @__PURE__ */ $e(no, [["__scopeId", "data-v-5789772e"]]), lo = ["d"], ao = {
  key: 1,
  class: "jf-icon jf-icon--text"
}, so = /* @__PURE__ */ q({
  name: "JfIcon",
  __name: "JfIcon",
  props: {
    name: {},
    size: { default: 16 }
  },
  setup(e) {
    const l = e, i = {
      // 工作台
      home: ["M3 11l9-8 9 8", "M5 9v12h14V9", "M9 21v-6h6v6"],
      // 发起申请（file-plus）
      apply: ["M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z", "M14 2v6h6", "M12 12v6", "M9 15h6"],
      // 我的待办（clipboard-list）
      todo: ["M8 2h8v4H8z", "M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2", "M9 12h6", "M9 16h6"],
      // 我的已办（check-circle）
      done: ["M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18z", "M8.5 12.5l2.5 2.5 5-5"],
      // 我发起的（file-text）
      mine: ["M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z", "M14 2v6h6", "M9 13h6", "M9 17h6"],
      // 我的抄送（send）
      cc: ["M22 2 11 13", "M22 2 15 22l-4-9-9-4z"],
      // 流程定义（package）
      define: ["M21 8v8a2 2 0 0 1-1 1.73l-7 4a2 2 0 0 1-2 0l-7-4A2 2 0 0 1 3 16V8a2 2 0 0 1 1-1.73l7-4a2 2 0 0 1 2 0l7 4A2 2 0 0 1 21 8z", "M3.3 7l8.7 5 8.7-5", "M12 22V12"],
      // 流程设计（pen-line）
      design: ["M12 20h9", "M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4z"],
      // 我的委托（repeat）
      surrogate: ["M17 2l4 4-4 4", "M3 11v-1a4 4 0 0 1 4-4h14", "M7 22l-4-4 4-4", "M21 13v1a4 4 0 0 1-4 4H3"],
      // 通用文档（卡片兜底图标）
      doc: ["M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z", "M14 2v6h6"],
      // 咖啡（空态）
      coffee: ["M17 8h1a4 4 0 1 1 0 8h-1", "M3 8h14v9a4 4 0 0 1-4 4H7a4 4 0 0 1-4-4z"],
      // 对勾
      check: ["M20 6 9 17l-5-5"],
      // 搜索
      search: ["M11 19a8 8 0 1 0 0-16 8 8 0 0 0 0 16z", "M21 21l-4.35-4.35"],
      // 刷新
      refresh: ["M21 12a9 9 0 1 1-2.64-6.36", "M21 3v6h-6"],
      // 用户
      user: ["M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2", "M12 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8z"]
    }, n = E(() => i[l.name] ?? null);
    return (s, c) => n.value ? (o(), u("svg", {
      key: 0,
      class: "jf-icon",
      style: ce({ width: `${e.size}px`, height: `${e.size}px` }),
      viewBox: "0 0 24 24",
      fill: "none",
      stroke: "currentColor",
      "stroke-width": "2",
      "stroke-linecap": "round",
      "stroke-linejoin": "round",
      "aria-hidden": "true"
    }, [
      (o(!0), u(G, null, le(n.value, (a, r) => (o(), u("path", {
        key: r,
        d: a
      }, null, 8, lo))), 128))
    ], 4)) : (o(), u("span", ao, w(e.name), 1));
  }
}), Pe = /* @__PURE__ */ $e(so, [["__scopeId", "data-v-acd21696"]]), oo = { class: "jf-tabs" }, io = {
  class: "jf-tabs__nav",
  role: "tablist"
}, ro = ["aria-selected", "onClick"], uo = { class: "jf-tabs__body" }, qt = /* @__PURE__ */ q({
  name: "JfTabs",
  __name: "JfTabs",
  props: {
    modelValue: {},
    tabs: {}
  },
  emits: ["update:modelValue"],
  setup(e, { emit: l }) {
    const i = l;
    return (n, s) => (o(), u("div", oo, [
      t("div", io, [
        (o(!0), u(G, null, le(e.tabs, (c) => (o(), u("button", {
          key: c.key,
          type: "button",
          role: "tab",
          class: ne(["jf-tabs__tab", { "jf-tabs__tab--active": e.modelValue === c.key }]),
          "aria-selected": e.modelValue === c.key,
          onClick: (a) => i("update:modelValue", c.key)
        }, w(c.label), 11, ro))), 128))
      ]),
      t("div", uo, [
        ke(n.$slots, "default")
      ])
    ]));
  }
}), co = { class: "jf-approval" }, fo = {
  key: 0,
  class: "jf-empty"
}, po = { class: "jf-timeline" }, vo = { class: "jf-timeline__content" }, mo = { class: "jf-timeline__head" }, ho = { class: "jf-muted" }, yo = { class: "jf-timeline__meta" }, go = {
  key: 0,
  class: "jf-muted"
}, bo = {
  class: "jf-table",
  style: { "margin-top": "16px" }
}, ko = { class: "jf-muted" }, jo = { class: "jf-muted" }, Dn = /* @__PURE__ */ q({
  name: "JfApprovalRecord",
  __name: "JfApprovalRecord",
  props: {
    records: {}
  },
  setup(e) {
    function l(c) {
      var a;
      return ((a = c.ext) == null ? void 0 : a.u_realName) || c.operator || "-";
    }
    function i(c) {
      var a, r;
      return ((a = c.ext) == null ? void 0 : a.submitType) ?? ((r = c.variable) == null ? void 0 : r.submitType);
    }
    function n(c) {
      var r, y;
      const a = ((r = c.variable) == null ? void 0 : r.tf_approvalComment) ?? ((y = c.ext) == null ? void 0 : y.tf_approvalComment);
      return a != null && a !== "" ? String(a) : "-";
    }
    function s(c) {
      const a = Number(i(c));
      return a === 2 || a === 20 ? "reject" : a === 1 || a === 0 || a === 5 ? "done" : "info";
    }
    return (c, a) => (o(), u("div", co, [
      e.records.length ? (o(), u(G, { key: 1 }, [
        t("ul", po, [
          (o(!0), u(G, null, le(e.records, (r, y) => (o(), u("li", {
            key: y,
            class: "jf-timeline__item"
          }, [
            t("span", {
              class: ne(["jf-timeline__dot", `jf-timeline__dot--${H(wn)(r.taskState)}`])
            }, null, 2),
            t("div", vo, [
              t("div", mo, [
                t("strong", null, w(r.displayName || r.taskName), 1),
                t("span", ho, w(H(xe)(r.finishTime, !0)), 1)
              ]),
              t("div", yo, [
                t("span", null, w(l(r)), 1),
                J(Oe, {
                  type: s(r)
                }, {
                  default: te(() => [
                    ee(w(H(an)(i(r))), 1)
                  ]),
                  _: 2
                }, 1032, ["type"]),
                n(r) !== "-" ? (o(), u("span", go, w(n(r)), 1)) : M("", !0)
              ])
            ])
          ]))), 128))
        ]),
        t("table", bo, [
          a[0] || (a[0] = t("thead", null, [
            t("tr", null, [
              t("th", null, "节点"),
              t("th", null, "处理人"),
              t("th", null, "操作"),
              t("th", null, "意见"),
              t("th", null, "时间")
            ])
          ], -1)),
          t("tbody", null, [
            (o(!0), u(G, null, le(e.records, (r, y) => (o(), u("tr", {
              key: "t" + y
            }, [
              t("td", null, [
                t("strong", null, w(r.displayName || r.taskName), 1)
              ]),
              t("td", null, w(l(r)), 1),
              t("td", null, [
                J(Oe, {
                  type: s(r)
                }, {
                  default: te(() => [
                    ee(w(H(an)(i(r))), 1)
                  ]),
                  _: 2
                }, 1032, ["type"])
              ]),
              t("td", ko, w(n(r)), 1),
              t("td", jo, w(H(xe)(r.finishTime, !0)), 1)
            ]))), 128))
          ])
        ])
      ], 64)) : (o(), u("div", fo, "暂无审批记录"))
    ]));
  }
}), $o = {
  key: 0,
  class: "jf-extras"
}, wo = {
  key: 0,
  class: "jf-form-item"
}, _o = {
  key: 1,
  class: "jf-form-item"
}, Co = {
  key: 2,
  class: "jf-form-item"
}, Io = ["disabled", "value"], xo = {
  key: 3,
  class: "jf-form-item"
}, Do = {
  key: 1,
  class: "jf-muted",
  style: { "margin-top": "4px" }
}, Rt = /* @__PURE__ */ q({
  name: "JfInitiateExtras",
  __name: "JfInitiateExtras",
  props: {
    graph: { default: null },
    taskId: { default: null },
    disabled: { type: Boolean, default: !1 },
    ccActors: { default: () => [] },
    nextOperators: { default: () => [] },
    applyReason: { default: "" },
    attachment: { default: "" }
  },
  emits: ["update:ccActors", "update:nextOperators", "update:applyReason", "update:attachment"],
  setup(e, { emit: l }) {
    const i = e, n = l, s = E(() => cl(i.graph)), { adapters: c } = je();
    async function a(r) {
      var v;
      const y = (v = r.target.files) == null ? void 0 : v[0];
      if (!y) {
        n("update:attachment", "");
        return;
      }
      if (c.upload)
        try {
          n("update:attachment", await c.upload(y));
        } catch {
          n("update:attachment", y.name);
        }
      else
        n("update:attachment", y.name);
    }
    return (r, y) => s.value.any ? (o(), u("div", $o, [
      s.value.selectUser ? (o(), u("div", wo, [
        y[3] || (y[3] = t("label", { class: "jf-form-label" }, "指定下一节点处理人", -1)),
        J(at, {
          "model-value": e.nextOperators,
          "task-id": e.taskId,
          scene: "nextOperator",
          disabled: e.disabled,
          placeholder: "搜索并选择处理人",
          "onUpdate:modelValue": y[0] || (y[0] = (v) => n("update:nextOperators", v))
        }, null, 8, ["model-value", "task-id", "disabled"])
      ])) : M("", !0),
      s.value.cc ? (o(), u("div", _o, [
        y[4] || (y[4] = t("label", { class: "jf-form-label" }, "抄送给", -1)),
        J(at, {
          "model-value": e.ccActors,
          "task-id": e.taskId,
          scene: "cc",
          disabled: e.disabled,
          placeholder: "搜索并选择抄送人",
          "onUpdate:modelValue": y[1] || (y[1] = (v) => n("update:ccActors", v))
        }, null, 8, ["model-value", "task-id", "disabled"])
      ])) : M("", !0),
      s.value.reason ? (o(), u("div", Co, [
        y[5] || (y[5] = t("label", { class: "jf-form-label" }, "申请理由", -1)),
        t("textarea", {
          class: "jf-input",
          rows: "3",
          disabled: e.disabled,
          value: e.applyReason,
          placeholder: "请输入申请理由",
          onInput: y[2] || (y[2] = (v) => n("update:applyReason", v.target.value))
        }, null, 40, Io)
      ])) : M("", !0),
      s.value.attachment ? (o(), u("div", xo, [
        y[6] || (y[6] = t("label", { class: "jf-form-label" }, "附件", -1)),
        e.disabled ? M("", !0) : (o(), u("input", {
          key: 0,
          class: "jf-input",
          type: "file",
          onChange: a
        }, null, 32)),
        e.attachment ? (o(), u("div", Do, w(e.attachment), 1)) : M("", !0)
      ])) : M("", !0)
    ])) : M("", !0);
  }
}), No = { class: "jf-layout" }, To = { class: "jf-layout__header" }, Po = { class: "jf-layout__logo" }, Mo = { class: "jf-layout__title" }, Eo = { class: "jf-layout__header-right" }, Lo = { class: "jf-layout__body" }, Ao = { class: "jf-layout__sider" }, So = { class: "jf-menu" }, Oo = ["onClick"], zo = { class: "jf-menu__icon" }, Bo = { class: "jf-layout__content" }, Uo = /* @__PURE__ */ q({
  name: "JfLayout",
  __name: "JfLayout",
  props: {
    menus: {},
    title: { default: "jeeflow 流程中心" },
    logo: {},
    defaultKey: {}
  },
  emits: ["select"],
  setup(e, { emit: l }) {
    var v;
    const i = e, n = l, { can: s } = je(), c = b(i.defaultKey ?? ((v = i.menus[0]) == null ? void 0 : v.key) ?? ""), a = E(
      () => i.menus.filter((h) => !h.perms || h.perms.length === 0 || s(h.perms))
    ), r = E(
      () => i.menus.find((h) => h.key === c.value) ?? null
    );
    be(() => i.defaultKey, (h) => {
      h && (c.value = h);
    });
    function y(h) {
      if (!h) return;
      const p = i.menus.find((f) => f.key === h);
      if (p != null && p.href) {
        window.open(p.href, "_blank");
        return;
      }
      c.value = h, n("select", h);
    }
    return (h, p) => (o(), u("div", No, [
      t("header", To, [
        t("div", {
          class: "jf-layout__brand",
          onClick: p[0] || (p[0] = (f) => {
            var j;
            return y((j = e.menus[0]) == null ? void 0 : j.key);
          })
        }, [
          t("span", Po, [
            e.logo ? (o(), u(G, { key: 1 }, [
              ee(w(e.logo), 1)
            ], 64)) : (o(), ae(Pe, {
              key: 0,
              name: "define",
              size: 22
            }))
          ]),
          t("span", Mo, w(e.title), 1)
        ]),
        t("div", Eo, [
          ke(h.$slots, "header-right", {}, void 0, !0)
        ])
      ]),
      t("div", Lo, [
        t("aside", Ao, [
          t("nav", So, [
            (o(!0), u(G, null, le(a.value, (f) => (o(), u("div", {
              key: f.key,
              class: ne(["jf-menu__item", { "jf-menu__item--active": f.key === c.value }]),
              onClick: (j) => y(f.key)
            }, [
              t("span", zo, [
                J(Pe, {
                  name: f.icon || "doc",
                  size: 17
                }, null, 8, ["name"])
              ]),
              t("span", null, w(f.title), 1)
            ], 10, Oo))), 128))
          ])
        ]),
        t("main", Bo, [
          ke(h.$slots, "default", { current: r.value }, void 0, !0)
        ])
      ])
    ]));
  }
}), Dc = /* @__PURE__ */ $e(Uo, [["__scopeId", "data-v-47d9ab87"]]);
let Vo = 0, Qe = null, Dt = [];
function Ro() {
  return Qe && document.body.contains(Qe) || (Qe = document.createElement("div"), Qe.className = "jf-toast-host", document.body.appendChild(Qe)), Qe;
}
function pn() {
  const e = Ro();
  e.innerHTML = Dt.map((l) => `<div class="jf-toast jf-toast--${l.type}">${Fo(l.msg)}</div>`).join("");
}
function Fo(e) {
  return e.replace(/[&<>"']/g, (l) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[l]);
}
function Ut(e, l) {
  const i = ++Vo;
  Dt.push({ id: i, type: e, msg: l }), pn(), setTimeout(() => {
    Dt = Dt.filter((n) => n.id !== i), pn();
  }, 2600);
}
const X = {
  success: (e) => Ut("success", e),
  error: (e) => Ut("error", e),
  info: (e) => Ut("info", e)
}, Jo = {
  key: 0,
  class: "jf-loading"
}, Yo = { class: "jf-drawer-actions" }, Wo = ["disabled"], Go = {
  key: 0,
  class: "jf-pane-flow"
}, Ho = {
  key: 1,
  class: "jf-empty"
}, Ko = /* @__PURE__ */ q({
  name: "JfStartDrawer",
  __name: "StartDrawer",
  props: {
    visible: { type: Boolean },
    define: {},
    title: { default: "发起流程" },
    width: { default: "60%" }
  },
  emits: ["update:visible", "started"],
  setup(e, { emit: l }) {
    const i = e, n = l, { api: s, getForm: c } = je(), a = b(!1), r = b(!1), y = b("form"), v = [
      { key: "form", label: "表单" },
      { key: "flow", label: "流程图" }
    ], h = b(""), p = b({}), f = b(null), j = b(null), g = b([]), C = b([]), D = b(""), T = b(""), N = E(() => {
      var S;
      return (S = i.define) != null && S.displayName ? `发起：${i.define.displayName}` : i.title;
    }), U = E(() => yt(f.value)), P = E(() => {
      var S;
      return Gt(f.value, Et(f.value), (S = U.value) == null ? void 0 : S.columns);
    }), B = E(() => {
      if (h.value && !Ht(h.value)) {
        const S = c(h.value, "start");
        if (S) return S;
      }
      return Xe;
    }), V = E(() => B.value !== Xe ? {} : {
      schema: U.value,
      fieldLabels: Wt(f.value),
      permissions: P.value,
      readonly: !1,
      fieldPrefix: "f_"
    });
    be(() => i.visible, async (S) => {
      if (S && (h.value = "", p.value = {}, f.value = null, y.value = "form", g.value = [], C.value = [], D.value = "", T.value = "", !!i.define)) {
        a.value = !0;
        try {
          let z = i.define.jsonObject;
          const W = i.define.processDefineId || i.define.id;
          !z && W && (z = (await s.processDefine.detail(W)).jsonObject), f.value = z || null, h.value = _n(z);
        } finally {
          a.value = !1;
        }
      }
    }, { immediate: !0 });
    async function F() {
      var W, fe, pe, $;
      const S = ((W = i.define) == null ? void 0 : W.processDefineId) || ((fe = i.define) == null ? void 0 : fe.id);
      if (!S) {
        X.error("缺少 processDefineId，无法发起");
        return;
      }
      const z = ($ = (pe = j.value) == null ? void 0 : pe.validate) == null ? void 0 : $.call(pe);
      if (z) {
        X.error(z);
        return;
      }
      r.value = !0;
      try {
        const _ = {};
        for (const [L, ie] of Object.entries(p.value))
          ie === "" || ie == null || (_[L.startsWith("f_") ? L : `f_${L}`] = ie);
        g.value.length && (_.f_ccActors = g.value), C.value.length && (_.f_nextNodeOperator = C.value), D.value.trim() && (_.f_applyReason = D.value.trim()), T.value && (_.f_attachment = T.value);
        const x = await s.processDefine.startAndExecute(S, _);
        X.success("发起成功"), n("started", x.processInstanceId), n("update:visible", !1);
      } catch (_) {
        X.error(_.message || "发起失败");
      } finally {
        r.value = !1;
      }
    }
    return (S, z) => (o(), ae(Ve, {
      visible: e.visible,
      title: N.value,
      width: e.width,
      fill: "",
      "onUpdate:visible": z[7] || (z[7] = (W) => n("update:visible", W))
    }, {
      default: te(() => [
        a.value ? (o(), u("div", Jo, "加载中...")) : (o(), ae(qt, {
          key: 1,
          modelValue: y.value,
          "onUpdate:modelValue": z[6] || (z[6] = (W) => y.value = W),
          tabs: v
        }, {
          default: te(() => [
            de(t("div", null, [
              B.value ? (o(), ae(Mt(B.value), ft({
                key: 0,
                ref_key: "formRef",
                ref: j,
                modelValue: p.value,
                "onUpdate:modelValue": z[0] || (z[0] = (W) => p.value = W)
              }, V.value, { onSubmit: F }), null, 16, ["modelValue"])) : M("", !0),
              J(Rt, {
                graph: f.value,
                "cc-actors": g.value,
                "onUpdate:ccActors": z[1] || (z[1] = (W) => g.value = W),
                "next-operators": C.value,
                "onUpdate:nextOperators": z[2] || (z[2] = (W) => C.value = W),
                "apply-reason": D.value,
                "onUpdate:applyReason": z[3] || (z[3] = (W) => D.value = W),
                attachment: T.value,
                "onUpdate:attachment": z[4] || (z[4] = (W) => T.value = W)
              }, null, 8, ["graph", "cc-actors", "next-operators", "apply-reason", "attachment"]),
              t("div", Yo, [
                t("button", {
                  class: "jf-btn jf-btn--ghost",
                  onClick: z[5] || (z[5] = (W) => n("update:visible", !1))
                }, "取消"),
                t("button", {
                  class: "jf-btn jf-btn--primary",
                  disabled: r.value,
                  onClick: F
                }, w(r.value ? "发起中..." : "发起"), 9, Wo)
              ])
            ], 512), [
              [Ye, y.value === "form"]
            ]),
            de(t("div", null, [
              f.value ? (o(), u("div", Go, [
                J(Lt, {
                  "graph-data": f.value,
                  height: "100%"
                }, null, 8, ["graph-data"])
              ])) : (o(), u("div", Ho, "暂无流程图"))
            ], 512), [
              [Ye, y.value === "flow"]
            ])
          ]),
          _: 1
        }, 8, ["modelValue"]))
      ]),
      _: 1
    }, 8, ["visible", "title", "width"]));
  }
}), Qo = {
  key: 0,
  class: "jf-loading"
}, Xo = {
  key: 0,
  class: "jf-section-title"
}, qo = { class: "jf-approve-actions" }, Zo = ["disabled"], ei = { class: "jf-form-item" }, ti = { class: "jf-approve-actions" }, ni = ["disabled"], li = ["disabled"], ai = ["disabled"], si = ["disabled"], oi = ["disabled"], ii = ["disabled"], ri = ["disabled"], di = ["disabled"], ui = {
  key: 0,
  class: "jf-pane-flow"
}, ci = {
  key: 1,
  class: "jf-empty"
}, fi = {
  key: 2,
  class: "jf-empty"
}, pi = {
  key: 0,
  class: "jf-loading"
}, vi = {
  key: 1,
  class: "jf-list"
}, mi = ["onClick"], hi = {
  key: 2,
  class: "jf-empty"
}, yi = { class: "jf-form-item" }, gi = { class: "jf-drawer-actions" }, bi = ["disabled"], Nn = /* @__PURE__ */ q({
  name: "JfApproveDrawer",
  __name: "ApproveDrawer",
  props: {
    visible: { type: Boolean },
    taskId: {},
    width: { default: "60%" },
    readonly: { type: Boolean, default: !1 }
  },
  emits: ["update:visible", "changed"],
  setup(e, { emit: l }) {
    const i = e, n = l, { api: s, getForm: c } = je(), a = b(!1), r = b(null), y = b(null), v = b([]), h = b([]), p = b({}), f = b({}), j = b(""), g = b(!1), C = b("detail"), D = b(null), T = b(!1), N = b(!1), U = b([]), P = b(!1), B = b(!1), V = b([]), F = b(!1), S = b([]), z = b([]), W = b(""), fe = b(""), pe = [
      { key: "detail", label: "详情" },
      { key: "flow", label: "流程图" },
      { key: "record", label: "审批记录" }
    ], $ = E(() => r.value ? `办理：${r.value.displayName}` : "办理任务"), _ = E(() => {
      var Y;
      return ((Y = r.value) == null ? void 0 : Y.jsonObject) || null;
    }), x = E(() => {
      var Y;
      return ((Y = r.value) == null ? void 0 : Y.taskState) === 10;
    }), L = E(() => {
      var O, ge;
      const Y = r.value;
      if ((O = Y == null ? void 0 : Y.ext) != null && O.isFirstTaskNode || Y != null && Y.isFirstTaskNode) return !0;
      const R = Et(_.value);
      return !!(R && (R.id === (Y == null ? void 0 : Y.taskName) || ((ge = R.properties) == null ? void 0 : ge.name) === (Y == null ? void 0 : Y.taskName)));
    }), ie = E(() => {
      var R, O;
      const Y = r.value;
      return Y ? il(_.value, Y.taskName) || { properties: { ...Y.taskModel, field: ((R = Y.taskModel) == null ? void 0 : R.ext) || ((O = Y.taskModel) == null ? void 0 : O.field) } } : null;
    }), K = E(() => yt(_.value)), Q = E(() => {
      var Y;
      return Gt(_.value, ie.value, (Y = K.value) == null ? void 0 : Y.columns);
    }), Z = E(() => Wt(_.value)), re = E(() => {
      var Y;
      return ul(ie.value, (Y = r.value) == null ? void 0 : Y.performType);
    }), ye = E(() => {
      var Y;
      return i.readonly || !x.value ? !0 : L.value ? !1 : !((Y = _.value) != null && Y.enableFieldPerm);
    });
    function oe(Y) {
      return re.value.includes(Y);
    }
    const we = E(() => {
      var Y;
      return ((Y = r.value) == null ? void 0 : Y.formKey) ?? "";
    }), ue = E(() => {
      if (!we.value || Ht(we.value))
        return K.value ? Xe : null;
      const Y = c(we.value, "approve");
      return Y || (K.value ? Xe : null);
    }), Ee = E(() => ue.value === Xe ? {
      schema: K.value,
      fieldLabels: Z.value,
      permissions: Q.value,
      readonly: i.readonly,
      fieldPrefix: "tf_"
    } : { task: r.value });
    be(() => [i.visible, i.taskId], async ([Y, R]) => {
      if (!(!Y || !R)) {
        a.value = !0, r.value = null, y.value = null, v.value = [], h.value = [], p.value = {}, f.value = {}, j.value = "", V.value = [], S.value = [], z.value = [], W.value = "", fe.value = "", C.value = "detail";
        try {
          r.value = await s.processTask.detail(R), f.value = Vt(r.value);
          const O = r.value.processInstanceId, ge = [
            s.processInstance.highLight(O).then((Le) => {
              y.value = Le;
            }).catch(() => {
              y.value = null;
            }),
            s.processInstance.approvalRecord(O).then((Le) => {
              v.value = Le;
            }).catch(() => {
              v.value = [];
            }),
            s.processInstance.getAssigneeTextData(O).then((Le) => {
              h.value = Le;
            }).catch(() => {
              h.value = [];
            })
          ];
          Object.keys(f.value).length || ge.push(
            s.processInstance.detail(O).then((Le) => {
              var kt;
              !((kt = r.value) != null && kt.jsonObject) && Le.jsonObject && (r.value.jsonObject = Le.jsonObject);
              const bt = Vt(Le);
              Object.keys(bt).length && (f.value = bt);
            }).catch(() => {
            })
          ), await Promise.all(ge);
        } finally {
          a.value = !1;
        }
      }
    }, { immediate: !0 });
    async function ve() {
      if (T.value = !0, U.value = [], !!r.value) {
        N.value = !0;
        try {
          U.value = await s.processTask.jumpAbleTaskNameList(r.value.processInstanceId);
        } catch {
          U.value = [];
        } finally {
          N.value = !1;
        }
      }
    }
    function Ge() {
      const Y = {};
      for (const [R, O] of Object.entries(p.value))
        O === "" || O == null || (Y[R.startsWith("tf_") ? R : `tf_${R}`] = O);
      return j.value.trim() && !("tf_approvalComment" in Y) && (Y.tf_approvalComment = j.value.trim()), S.value.length && (Y.tf_ccActors = S.value), z.value.length && (Y.tf_nextNodeOperator = z.value), Y;
    }
    function De() {
      const Y = {};
      for (const [R, O] of Object.entries(f.value))
        O === "" || O == null || (Y[R.startsWith("f_") ? R : `f_${R}`] = O);
      return S.value.length && (Y.f_ccActors = S.value), z.value.length && (Y.f_nextNodeOperator = z.value), W.value.trim() && (Y.f_applyReason = W.value.trim()), fe.value && (Y.f_attachment = fe.value), Y;
    }
    async function ze(Y, R = {}) {
      var O;
      if (i.taskId) {
        g.value = !0;
        try {
          const ge = !L.value && ((O = _.value) != null && O.enableFieldPerm) ? De() : {};
          await s.processTask.execute(i.taskId, Y, { ...Ge(), ...ge, ...R }), X.success("办理成功"), n("changed"), n("update:visible", !1);
        } catch (ge) {
          X.error(ge.message || "办理失败");
        } finally {
          g.value = !1;
        }
      }
    }
    async function Ze() {
      var R, O;
      const Y = (O = (R = D.value) == null ? void 0 : R.validate) == null ? void 0 : O.call(R);
      if (Y) {
        X.error(Y);
        return;
      }
      await ze(Ke.RE_APPLY, De());
    }
    function Re() {
      return ze(Ke.COUNTERSIGN_DISAGREE, { countersignDisagreeFlag: !0 });
    }
    async function Fe(Y) {
      await ze(Ke.JUMP, { taskName: Y }), T.value = !1;
    }
    async function At() {
      if (!(!i.taskId || !V.value.length)) {
        F.value = !0;
        try {
          P.value ? await s.processTask.surrogate(i.taskId, V.value) : await s.processTask.addCandidate(i.taskId, V.value), P.value = !1, B.value = !1, V.value = [], n("changed");
        } finally {
          F.value = !1;
        }
      }
    }
    return (Y, R) => (o(), ae(Ve, {
      visible: e.visible,
      title: $.value,
      width: e.width,
      fill: "",
      "onUpdate:visible": R[20] || (R[20] = (O) => n("update:visible", O))
    }, {
      default: te(() => [
        a.value ? (o(), u("div", Qo, "加载中...")) : r.value ? (o(), ae(qt, {
          key: 1,
          modelValue: C.value,
          "onUpdate:modelValue": R[15] || (R[15] = (O) => C.value = O),
          tabs: pe
        }, {
          default: te(() => [
            de(t("div", null, [
              K.value || Object.keys(f.value).length ? (o(), u("h3", Xo, "申请信息")) : M("", !0),
              K.value || Object.keys(f.value).length ? (o(), ae(H(Xe), {
                key: 1,
                ref_key: "bizFormRef",
                ref: D,
                modelValue: f.value,
                "onUpdate:modelValue": R[0] || (R[0] = (O) => f.value = O),
                schema: K.value,
                "field-labels": Z.value,
                permissions: Q.value,
                readonly: ye.value,
                "field-prefix": "f_"
              }, null, 8, ["modelValue", "schema", "field-labels", "permissions", "readonly"])) : M("", !0),
              ue.value && !L.value ? (o(), ae(Mt(ue.value), ft({
                key: 2,
                modelValue: p.value,
                "onUpdate:modelValue": R[1] || (R[1] = (O) => p.value = O)
              }, Ee.value), null, 16, ["modelValue"])) : M("", !0),
              !e.readonly && x.value ? (o(), u(G, { key: 3 }, [
                L.value ? (o(), u(G, { key: 0 }, [
                  J(Rt, {
                    graph: _.value,
                    "cc-actors": S.value,
                    "onUpdate:ccActors": R[2] || (R[2] = (O) => S.value = O),
                    "next-operators": z.value,
                    "onUpdate:nextOperators": R[3] || (R[3] = (O) => z.value = O),
                    "apply-reason": W.value,
                    "onUpdate:applyReason": R[4] || (R[4] = (O) => W.value = O),
                    attachment: fe.value,
                    "onUpdate:attachment": R[5] || (R[5] = (O) => fe.value = O)
                  }, null, 8, ["graph", "cc-actors", "next-operators", "apply-reason", "attachment"]),
                  t("div", qo, [
                    t("button", {
                      class: "jf-btn jf-btn--primary",
                      disabled: g.value,
                      onClick: Ze
                    }, "重新提交", 8, Zo)
                  ])
                ], 64)) : (o(), u(G, { key: 1 }, [
                  t("div", ei, [
                    R[21] || (R[21] = t("label", { class: "jf-form-label" }, "审批意见", -1)),
                    de(t("textarea", {
                      "onUpdate:modelValue": R[6] || (R[6] = (O) => j.value = O),
                      class: "jf-input",
                      rows: "3",
                      placeholder: "请输入审批意见（可选）"
                    }, null, 512), [
                      [Te, j.value]
                    ])
                  ]),
                  J(Rt, {
                    graph: _.value,
                    "task-id": e.taskId,
                    "cc-actors": S.value,
                    "onUpdate:ccActors": R[7] || (R[7] = (O) => S.value = O),
                    "next-operators": z.value,
                    "onUpdate:nextOperators": R[8] || (R[8] = (O) => z.value = O)
                  }, null, 8, ["graph", "task-id", "cc-actors", "next-operators"]),
                  t("div", ti, [
                    oe("AGREE") ? (o(), u("button", {
                      key: 0,
                      class: "jf-btn jf-btn--primary",
                      disabled: g.value,
                      onClick: R[9] || (R[9] = (O) => ze(H(Ke).AGREE))
                    }, "同意", 8, ni)) : M("", !0),
                    oe("REJECT") ? (o(), u("button", {
                      key: 1,
                      class: "jf-btn jf-btn--danger",
                      disabled: g.value,
                      onClick: R[10] || (R[10] = (O) => ze(H(Ke).REJECT))
                    }, "拒绝", 8, li)) : M("", !0),
                    oe("ROLLBACK") ? (o(), u("button", {
                      key: 2,
                      class: "jf-btn jf-btn--ghost",
                      disabled: g.value,
                      onClick: R[11] || (R[11] = (O) => ze(H(Ke).ROLLBACK))
                    }, "退回上一步", 8, ai)) : M("", !0),
                    oe("ROLLBACK_TO_OPERATOR") ? (o(), u("button", {
                      key: 3,
                      class: "jf-btn jf-btn--ghost",
                      disabled: g.value,
                      onClick: R[12] || (R[12] = (O) => ze(H(Ke).ROLLBACK_TO_OPERATOR))
                    }, "退回发起人", 8, si)) : M("", !0),
                    oe("COUNTERSIGN_DISAGREE") ? (o(), u("button", {
                      key: 4,
                      class: "jf-btn jf-btn--danger",
                      disabled: g.value,
                      onClick: Re
                    }, "会签拒绝", 8, oi)) : M("", !0),
                    oe("JUMP") ? (o(), u("button", {
                      key: 5,
                      class: "jf-btn jf-btn--ghost",
                      disabled: g.value,
                      onClick: ve
                    }, "跳转", 8, ii)) : M("", !0),
                    t("button", {
                      class: "jf-btn jf-btn--ghost",
                      disabled: g.value,
                      onClick: R[13] || (R[13] = (O) => P.value = !0)
                    }, "转办", 8, ri),
                    oe("ADD_CANDIDATE") ? (o(), u("button", {
                      key: 6,
                      class: "jf-btn jf-btn--ghost",
                      disabled: g.value,
                      onClick: R[14] || (R[14] = (O) => B.value = !0)
                    }, "加签", 8, di)) : M("", !0)
                  ])
                ], 64))
              ], 64)) : M("", !0)
            ], 512), [
              [Ye, C.value === "detail"]
            ]),
            de(t("div", null, [
              _.value ? (o(), u("div", ui, [
                J(Lt, {
                  "graph-data": _.value,
                  "high-light": y.value,
                  "assignee-text-data": h.value,
                  height: "100%"
                }, null, 8, ["graph-data", "high-light", "assignee-text-data"])
              ])) : (o(), u("div", ci, "暂无流程图"))
            ], 512), [
              [Ye, C.value === "flow"]
            ]),
            de(t("div", null, [
              J(Dn, { records: v.value }, null, 8, ["records"])
            ], 512), [
              [Ye, C.value === "record"]
            ])
          ]),
          _: 1
        }, 8, ["modelValue"])) : (o(), u("div", fi, "任务不存在")),
        J(Ve, {
          visible: T.value,
          "onUpdate:visible": R[16] || (R[16] = (O) => T.value = O),
          title: "跳转到节点",
          width: "420px"
        }, {
          default: te(() => [
            N.value ? (o(), u("div", pi, "加载中...")) : U.value.length ? (o(), u("div", vi, [
              (o(!0), u(G, null, le(U.value, (O) => (o(), u("button", {
                key: O.value,
                class: "jf-list-item",
                onClick: (ge) => Fe(O.value)
              }, w(O.label), 9, mi))), 128))
            ])) : (o(), u("div", hi, "无可跳转节点"))
          ]),
          _: 1
        }, 8, ["visible"]),
        J(Ve, {
          title: P.value ? "转办（指定处理人）" : "加签（追加参与人）",
          visible: P.value || B.value,
          width: "480px",
          "onUpdate:visible": R[19] || (R[19] = (O) => {
            P.value = O, B.value = O;
          })
        }, {
          default: te(() => [
            t("div", yi, [
              R[22] || (R[22] = t("label", { class: "jf-form-label" }, "选择用户", -1)),
              J(at, {
                modelValue: V.value,
                "onUpdate:modelValue": R[17] || (R[17] = (O) => V.value = O),
                "task-id": B.value ? e.taskId : null,
                scene: B.value ? "candidate" : "surrogate",
                placeholder: "搜索姓名/工号"
              }, null, 8, ["modelValue", "task-id", "scene"])
            ]),
            t("div", gi, [
              t("button", {
                class: "jf-btn jf-btn--ghost",
                onClick: R[18] || (R[18] = (O) => {
                  P.value = !1, B.value = !1;
                })
              }, "取消"),
              t("button", {
                class: "jf-btn jf-btn--primary",
                disabled: F.value || !V.value.length,
                onClick: At
              }, "确定", 8, bi)
            ])
          ]),
          _: 1
        }, 8, ["title", "visible"])
      ]),
      _: 1
    }, 8, ["visible", "title", "width"]));
  }
}), ki = {
  key: 0,
  class: "jf-loading"
}, ji = {
  key: 1,
  class: "jf-detail-body"
}, $i = { class: "jf-detail-meta" }, wi = { key: 0 }, _i = {
  key: 0,
  class: "jf-progress-panel"
}, Ci = { class: "jf-progress-title" }, Ii = {
  key: 0,
  class: "jf-muted"
}, xi = { class: "jf-progress-members" }, Di = {
  key: 1,
  class: "jf-section-title"
}, Ni = { class: "jf-detail-actions" }, Ti = ["disabled"], Pi = ["disabled"], Mi = {
  key: 0,
  class: "jf-pane-flow"
}, Ei = {
  key: 1,
  class: "jf-empty"
}, Li = {
  key: 2,
  class: "jf-empty"
}, Ai = { class: "jf-form-item" }, Si = { class: "jf-drawer-actions" }, Oi = ["disabled"], zi = /* @__PURE__ */ q({
  name: "JfInstanceDetailDrawer",
  __name: "InstanceDetailDrawer",
  props: {
    visible: { type: Boolean },
    instanceId: {},
    width: { default: "60%" }
  },
  emits: ["update:visible", "changed"],
  setup(e, { emit: l }) {
    const i = e, n = l, { api: s, can: c, getForm: a } = je(), r = b(!1), y = b(!1), v = b(null), h = b([]), p = b(null), f = b([]), j = b({}), g = b(null), C = b("detail"), D = b(!1), T = b([]), N = b(!1), U = [
      { key: "detail", label: "详情" },
      { key: "flow", label: "流程图" },
      { key: "record", label: "审批记录" }
    ], P = E(() => v.value ? `${v.value.displayName || "流程详情"} · ${Yt(v.value.state)}` : "流程详情"), B = E(() => {
      var K;
      return ((K = v.value) == null ? void 0 : K.activeTaskList) ?? [];
    }), V = E(
      () => !!B.value.find((K) => {
        var Q;
        return (Q = K.ext) == null ? void 0 : Q.isFirstTaskNode;
      })
    ), F = E(() => {
      var K;
      return ((K = v.value) == null ? void 0 : K.jsonObject) || null;
    }), S = E(() => yt(F.value)), z = E(() => {
      const K = _n(F.value);
      return K && !Ht(K) ? a(K, "detail") : null;
    }), W = E(() => {
      var K;
      return Gt(F.value, Et(F.value), (K = S.value) == null ? void 0 : K.columns);
    }), fe = E(() => Wt(F.value)), pe = E(() => f.value.map((K) => K.label || K.value).filter(Boolean).join("、")), $ = E(() => {
      var Z, re, ye, oe, we, ue;
      const K = (Z = p.value) == null ? void 0 : Z.nodeProgress;
      if (!K || !v.value) return [];
      const Q = [];
      for (const [Ee, ve] of Object.entries(K)) {
        if (!((re = ve == null ? void 0 : ve.members) != null && re.length) || !ve.members.some((De) => De.active) && ve.members.every((De) => De.done)) continue;
        const Ge = (we = (oe = (ye = v.value.jsonObject) == null ? void 0 : ye.nodes) == null ? void 0 : oe.find) == null ? void 0 : we.call(oe, (De) => De.id === Ee);
        Q.push({
          node: Ee,
          displayName: ((ue = Ge == null ? void 0 : Ge.text) == null ? void 0 : ue.value) || Ee,
          type: ve.type,
          members: ve.members
        });
      }
      return Q;
    });
    be(() => [i.visible, i.instanceId], async ([K, Q]) => {
      if (!(!K || !Q)) {
        r.value = !0, v.value = null, h.value = [], p.value = null, f.value = [], j.value = {}, C.value = "detail";
        try {
          await _();
        } finally {
          r.value = !1;
        }
      }
    }, { immediate: !0 });
    async function _() {
      if (!i.instanceId) return;
      const [K, Q, Z] = await Promise.all([
        s.processInstance.detail(i.instanceId),
        s.processInstance.approvalRecord(i.instanceId),
        s.processInstance.highLight(i.instanceId)
      ]);
      v.value = K, h.value = Q, p.value = Z, j.value = Vt(K);
      try {
        f.value = await s.processInstance.getAssigneeTextData(i.instanceId);
      } catch {
        f.value = [];
      }
    }
    async function x() {
      if (i.instanceId && window.confirm("确认撤回该流程？")) {
        y.value = !0;
        try {
          await s.processInstance.withdraw(i.instanceId), X.success("已撤回"), n("changed"), await _();
        } catch (K) {
          X.error(`撤回失败：${K.message}`);
        } finally {
          y.value = !1;
        }
      }
    }
    async function L() {
      var Z, re;
      const K = B.value.find((ye) => {
        var oe;
        return (oe = ye.ext) == null ? void 0 : oe.isFirstTaskNode;
      });
      if (!K) return;
      const Q = (re = (Z = g.value) == null ? void 0 : Z.validate) == null ? void 0 : re.call(Z);
      if (Q) {
        X.error(Q);
        return;
      }
      y.value = !0;
      try {
        const ye = {};
        for (const [oe, we] of Object.entries(j.value))
          we === "" || we == null || (ye[oe.startsWith("f_") ? oe : `f_${oe}`] = we);
        await s.processTask.execute(K.id, 5, ye), X.success("已重新提交"), n("changed"), await _();
      } catch (ye) {
        X.error(`重新提交失败：${ye.message}`);
      } finally {
        y.value = !1;
      }
    }
    async function ie() {
      if (!(!i.instanceId || !T.value.length)) {
        N.value = !0;
        try {
          await s.processInstance.createCCInstance(i.instanceId, T.value), X.success("抄送成功"), D.value = !1, T.value = [];
        } catch (K) {
          X.error(K.message || "抄送失败");
        } finally {
          N.value = !1;
        }
      }
    }
    return (K, Q) => (o(), ae(Ve, {
      visible: e.visible,
      title: P.value,
      width: e.width,
      fill: "",
      "onUpdate:visible": Q[7] || (Q[7] = (Z) => n("update:visible", Z))
    }, {
      default: te(() => [
        r.value ? (o(), u("div", ki, "加载中...")) : v.value ? (o(), u("div", ji, [
          J(qt, {
            modelValue: C.value,
            "onUpdate:modelValue": Q[3] || (Q[3] = (Z) => C.value = Z),
            tabs: U
          }, {
            default: te(() => [
              de(t("div", null, [
                t("div", $i, [
                  t("span", null, [
                    Q[8] || (Q[8] = ee("发起人: ", -1)),
                    t("strong", null, w(v.value.operator || "-"), 1)
                  ]),
                  t("span", null, [
                    Q[9] || (Q[9] = ee("流水号: ", -1)),
                    t("strong", null, w(v.value.businessNo || "-"), 1)
                  ]),
                  t("span", null, [
                    Q[10] || (Q[10] = ee("时间: ", -1)),
                    t("strong", null, w(H(xe)(v.value.createTime)), 1)
                  ]),
                  pe.value ? (o(), u("span", wi, [
                    Q[11] || (Q[11] = ee("当前处理人: ", -1)),
                    t("strong", null, w(pe.value), 1)
                  ])) : M("", !0)
                ]),
                $.value.length ? (o(), u("div", _i, [
                  (o(!0), u(G, null, le($.value, (Z) => (o(), u("div", {
                    key: Z.node,
                    class: "jf-progress-block"
                  }, [
                    t("div", Ci, [
                      ee(w(Z.displayName) + " ", 1),
                      Z.type ? (o(), u("span", Ii, "（" + w(Z.type === "SEQUENTIAL" ? "串行" : Z.type === "PARALLEL" ? "并行" : Z.type) + "会签）", 1)) : M("", !0)
                    ]),
                    t("div", xi, [
                      (o(!0), u(G, null, le(Z.members, (re) => (o(), u("span", {
                        key: re.id,
                        class: ne(["jf-progress-member", { "jf-progress-member--done": re.done, "jf-progress-member--active": re.active }])
                      }, w(re.name || re.id) + w(re.done ? " ✓" : ""), 3))), 128))
                    ])
                  ]))), 128))
                ])) : M("", !0),
                z.value || S.value || Object.keys(j.value).length ? (o(), u("h3", Di, "申请信息")) : M("", !0),
                z.value ? (o(), ae(Mt(z.value), {
                  key: 2,
                  ref_key: "bizFormRef",
                  ref: g,
                  modelValue: j.value,
                  "onUpdate:modelValue": Q[0] || (Q[0] = (Z) => j.value = Z),
                  view: !V.value
                }, null, 8, ["modelValue", "view"])) : S.value || Object.keys(j.value).length ? (o(), ae(H(Xe), {
                  key: 3,
                  ref_key: "bizFormRef",
                  ref: g,
                  modelValue: j.value,
                  "onUpdate:modelValue": Q[1] || (Q[1] = (Z) => j.value = Z),
                  schema: S.value,
                  "field-labels": fe.value,
                  permissions: W.value,
                  readonly: !V.value,
                  "field-prefix": "f_"
                }, null, 8, ["modelValue", "schema", "field-labels", "permissions", "readonly"])) : M("", !0),
                t("div", Ni, [
                  H(c)(["wf:processInstance:withdraw"]) && v.value.state === 10 && B.value.length ? (o(), u("button", {
                    key: 0,
                    class: "jf-btn jf-btn--ghost",
                    disabled: y.value,
                    onClick: x
                  }, "撤回", 8, Ti)) : M("", !0),
                  H(c)(["wf:processInstance:createCCInstance"]) ? (o(), u("button", {
                    key: 1,
                    class: "jf-btn jf-btn--ghost",
                    onClick: Q[2] || (Q[2] = (Z) => D.value = !0)
                  }, "抄送")) : M("", !0),
                  V.value ? (o(), u("button", {
                    key: 2,
                    class: "jf-btn jf-btn--primary",
                    disabled: y.value,
                    onClick: L
                  }, "重新提交", 8, Pi)) : M("", !0)
                ])
              ], 512), [
                [Ye, C.value === "detail"]
              ]),
              de(t("div", null, [
                v.value.jsonObject ? (o(), u("div", Mi, [
                  J(Lt, {
                    "graph-data": v.value.jsonObject,
                    "high-light": p.value,
                    "assignee-text-data": f.value,
                    height: "100%"
                  }, null, 8, ["graph-data", "high-light", "assignee-text-data"])
                ])) : (o(), u("div", Ei, "暂无流程图"))
              ], 512), [
                [Ye, C.value === "flow"]
              ]),
              de(t("div", null, [
                J(Dn, { records: h.value }, null, 8, ["records"])
              ], 512), [
                [Ye, C.value === "record"]
              ])
            ]),
            _: 1
          }, 8, ["modelValue"])
        ])) : (o(), u("div", Li, "实例不存在")),
        J(Ve, {
          visible: D.value,
          "onUpdate:visible": Q[6] || (Q[6] = (Z) => D.value = Z),
          title: "手动抄送",
          width: "480px"
        }, {
          default: te(() => [
            t("div", Ai, [
              Q[12] || (Q[12] = t("label", { class: "jf-form-label" }, "抄送人", -1)),
              J(at, {
                modelValue: T.value,
                "onUpdate:modelValue": Q[4] || (Q[4] = (Z) => T.value = Z),
                scene: "cc",
                placeholder: "搜索姓名/工号"
              }, null, 8, ["modelValue"])
            ]),
            t("div", Si, [
              t("button", {
                class: "jf-btn jf-btn--ghost",
                onClick: Q[5] || (Q[5] = (Z) => D.value = !1)
              }, "取消"),
              t("button", {
                class: "jf-btn jf-btn--primary",
                disabled: N.value || !T.value.length,
                onClick: ie
              }, "确定", 8, Oi)
            ])
          ]),
          _: 1
        }, 8, ["visible"])
      ]),
      _: 1
    }, 8, ["visible", "title", "width"]));
  }
}), gt = /* @__PURE__ */ $e(zi, [["__scopeId", "data-v-5553075e"]]), Bi = { class: "jf-page jf-workbench" }, Ui = { class: "jf-page-title" }, Vi = { class: "wb-cards" }, Ri = ["onClick"], Fi = { class: "wb-card__num" }, Ji = { class: "wb-card__label" }, Yi = {
  key: 0,
  class: "jf-empty"
}, Wi = { class: "wb-cards wb-cards--stats" }, Gi = { class: "wb-card wb-card--plain" }, Hi = { class: "wb-card__num" }, Ki = { class: "wb-card wb-card--plain" }, Qi = { class: "wb-card__num" }, Xi = { class: "wb-card wb-card--plain" }, qi = { class: "wb-card__num" }, Zi = { class: "wb-card wb-card--plain" }, er = { class: "wb-card__num" }, tr = { class: "wb-card wb-card--plain" }, nr = { class: "wb-card__num" }, lr = { class: "wb-card wb-card--plain" }, ar = { class: "wb-card__num" }, sr = { class: "wb-card wb-card--plain" }, or = { class: "wb-card__num" }, ir = {
  key: 0,
  class: "wb-card wb-card--plain"
}, rr = { class: "wb-card__num wb-card__num--warn" }, dr = { class: "wb-stats-grid" }, ur = { class: "wb-panel" }, cr = {
  key: 0,
  class: "wb-trend"
}, fr = ["title"], pr = { class: "wb-trend__bars" }, vr = { class: "wb-trend__label" }, mr = {
  key: 1,
  class: "jf-empty"
}, hr = { class: "wb-panel" }, yr = {
  key: 0,
  class: "jf-table wb-table-sm"
}, gr = { class: "jf-num" }, br = { class: "jf-muted jf-num" }, kr = {
  key: 1,
  class: "jf-empty"
}, jr = { class: "wb-panel" }, $r = {
  key: 0,
  class: "wb-dist"
}, wr = ["title"], _r = { class: "wb-dist__label" }, Cr = { class: "wb-dist__track" }, Ir = { class: "wb-dist__num" }, xr = {
  key: 1,
  class: "jf-empty"
}, Dr = { class: "jf-section-title" }, Nr = {
  key: 2,
  class: "jf-loading"
}, Tr = {
  key: 0,
  class: "jf-table"
}, Pr = { class: "jf-muted" }, Mr = { class: "jf-btn-row" }, Er = ["onClick"], Lr = ["onClick"], Ar = {
  key: 1,
  class: "jf-empty"
}, Sr = /* @__PURE__ */ q({
  name: "JfWorkbenchPage",
  __name: "WorkbenchPage",
  emits: ["goto"],
  setup(e, { emit: l }) {
    const i = l, { api: n } = je(), s = b(!1), c = b([]), a = b(0), r = Ue([
      { key: "todo", label: "待办", count: null },
      { key: "done", label: "在办（已处理）", count: null },
      { key: "mine", label: "我发起的", count: null },
      { key: "cc", label: "抄送我的", count: null }
    ]), y = b(null), v = b([]), h = b([]), p = b([]), f = b(""), j = {
      10: "进行中",
      20: "已完成",
      30: "已撤回",
      40: "强行终止",
      45: "已拒绝",
      50: "挂起"
    }, g = ($) => j[$] ?? $;
    function C($) {
      return $ == null ? "-" : $ < 60 ? `${$} 秒` : $ < 3600 ? `${Math.round($ / 60)} 分钟` : $ < 86400 ? `${($ / 3600).toFixed(1)} 小时` : `${($ / 86400).toFixed(1)} 天`;
    }
    const D = ($) => $ == null ? "-" : `${($ * 100).toFixed(1)}%`, T = () => Math.max(1, ...v.value.map(($) => Math.max($.started, $.finished))), N = ($) => `${Math.round($ / T() * 100)}%`, U = () => Math.max(1, ...p.value.map(($) => $.count)), P = ($) => `${Math.round($ / U() * 100)}%`;
    function B() {
      const $ = (L) => {
        const ie = (K) => String(K).padStart(2, "0");
        return `${L.getFullYear()}-${ie(L.getMonth() + 1)}-${ie(L.getDate())}`;
      }, _ = /* @__PURE__ */ new Date(), x = /* @__PURE__ */ new Date();
      return x.setDate(_.getDate() - 6), { start: `${$(x)} 00:00:00`, end: `${$(_)} 23:59:59` };
    }
    const V = b(!1), F = b(null), S = b(!1), z = b(null);
    async function W() {
      var $;
      s.value = !0;
      try {
        const _ = B(), [x, L, ie, K, Q, Z, re, ye] = await Promise.allSettled([
          n.processTask.todoList({ pageNum: 1, pageSize: 5 }),
          n.processTask.doneList({ pageNum: 1, pageSize: 1 }),
          n.processInstance.page({ pageNum: 1, pageSize: 1 }),
          n.processInstance.ccList({ pageNum: 1, pageSize: 1 }),
          n.processInstance.statsOverview(),
          n.processInstance.statsTrend({ ..._, granularity: "day" }),
          n.processInstance.statsGroup({ dimension: "define", limit: 5 }),
          n.processInstance.statsGroup({ dimension: "state" })
        ]);
        x.status === "fulfilled" && (c.value = x.value.rows, a.value = x.value.recordCount, r[0].count = x.value.recordCount), L.status === "fulfilled" && (r[1].count = L.value.recordCount), ie.status === "fulfilled" && (r[2].count = ie.value.recordCount), K.status === "fulfilled" && (r[3].count = K.value.recordCount), Q.status === "fulfilled" && (y.value = Q.value), Z.status === "fulfilled" && (v.value = Z.value), re.status === "fulfilled" && (h.value = re.value), ye.status === "fulfilled" && (p.value = ye.value);
        const oe = [Q, Z, re, ye].filter((we) => we.status === "rejected");
        oe.length === 4 ? f.value = oe[0].status === "rejected" ? ($ = oe[0].reason) == null ? void 0 : $.message : "未知错误" : f.value = "";
      } finally {
        s.value = !1;
      }
    }
    function fe($) {
      F.value = $, V.value = !0;
    }
    function pe($) {
      z.value = $, S.value = !0;
    }
    return he(W), ($, _) => (o(), u("div", Bi, [
      t("h2", Ui, [
        J(Pe, {
          name: "home",
          size: 18
        }),
        _[3] || (_[3] = ee(" 工作台", -1))
      ]),
      t("div", Vi, [
        (o(!0), u(G, null, le(r, (x) => (o(), u("div", {
          key: x.key,
          class: "wb-card",
          onClick: (L) => i("goto", x.key)
        }, [
          t("div", Fi, w(x.count == null ? "-" : x.count), 1),
          t("div", Ji, w(x.label), 1)
        ], 8, Ri))), 128))
      ]),
      _[18] || (_[18] = t("h3", { class: "jf-section-title" }, [
        ee("全局概览 "),
        t("span", { class: "jf-muted wb-stats-src" }, "stats/overview · trend · group")
      ], -1)),
      f.value ? (o(), u("div", Yi, "全局统计暂不可用：" + w(f.value), 1)) : y.value ? (o(), u(G, { key: 1 }, [
        t("div", Wi, [
          t("div", Gi, [
            t("div", Hi, w(y.value.total), 1),
            _[4] || (_[4] = t("div", { class: "wb-card__label" }, "实例总数", -1))
          ]),
          t("div", Ki, [
            t("div", Qi, w(y.value.inProgress), 1),
            _[5] || (_[5] = t("div", { class: "wb-card__label" }, "进行中", -1))
          ]),
          t("div", Xi, [
            t("div", qi, w(y.value.completed), 1),
            _[6] || (_[6] = t("div", { class: "wb-card__label" }, "已完成", -1))
          ]),
          t("div", Zi, [
            t("div", er, w(y.value.todayNew), 1),
            _[7] || (_[7] = t("div", { class: "wb-card__label" }, "今日新增", -1))
          ]),
          t("div", tr, [
            t("div", nr, w(C(y.value.avgDurationSeconds)), 1),
            _[8] || (_[8] = t("div", { class: "wb-card__label" }, "平均办结时长", -1))
          ]),
          t("div", lr, [
            t("div", ar, w(D(y.value.rejectRate)), 1),
            _[9] || (_[9] = t("div", { class: "wb-card__label" }, "驳回率", -1))
          ]),
          t("div", sr, [
            t("div", or, w(y.value.pendingTaskCount), 1),
            _[10] || (_[10] = t("div", { class: "wb-card__label" }, "积压任务", -1))
          ]),
          y.value.overdueTaskCount > 0 ? (o(), u("div", ir, [
            t("div", rr, w(y.value.overdueTaskCount), 1),
            _[11] || (_[11] = t("div", { class: "wb-card__label" }, "逾期任务", -1))
          ])) : M("", !0)
        ]),
        t("div", dr, [
          t("div", ur, [
            _[12] || (_[12] = t("h4", { class: "wb-panel__title" }, [
              ee("近 7 天趋势 "),
              t("span", { class: "jf-muted" }, "发起 / 办结")
            ], -1)),
            v.value.length ? (o(), u("div", cr, [
              (o(!0), u(G, null, le(v.value, (x) => (o(), u("div", {
                key: x.bucket,
                class: "wb-trend__col",
                title: `${x.bucket}：发起 ${x.started} / 办结 ${x.finished}`
              }, [
                t("div", pr, [
                  t("div", {
                    class: "wb-trend__bar wb-trend__bar--s",
                    style: ce({ height: N(x.started) })
                  }, null, 4),
                  t("div", {
                    class: "wb-trend__bar wb-trend__bar--f",
                    style: ce({ height: N(x.finished) })
                  }, null, 4)
                ]),
                t("div", vr, w(x.bucket.slice(5)), 1)
              ], 8, fr))), 128))
            ])) : (o(), u("div", mr, "暂无趋势数据"))
          ]),
          t("div", hr, [
            _[13] || (_[13] = t("h4", { class: "wb-panel__title" }, [
              ee("流程 Top 5 "),
              t("span", { class: "jf-muted" }, "group/define")
            ], -1)),
            h.value.length ? (o(), u("table", yr, [
              t("tbody", null, [
                (o(!0), u(G, null, le(h.value, (x) => (o(), u("tr", {
                  key: x.key
                }, [
                  t("td", null, w(x.label || x.key), 1),
                  t("td", gr, w(x.count), 1),
                  t("td", br, w(x.avgDurationSeconds != null ? C(x.avgDurationSeconds) : "-"), 1)
                ]))), 128))
              ])
            ])) : (o(), u("div", kr, "暂无实例数据"))
          ]),
          t("div", jr, [
            _[14] || (_[14] = t("h4", { class: "wb-panel__title" }, [
              ee("状态分布 "),
              t("span", { class: "jf-muted" }, "group/state")
            ], -1)),
            p.value.length ? (o(), u("div", $r, [
              (o(!0), u(G, null, le(p.value, (x) => (o(), u("div", {
                key: x.key,
                class: "wb-dist__row",
                title: `${g(x.key)}：${x.count}`
              }, [
                t("span", _r, w(g(x.key)), 1),
                t("span", Cr, [
                  t("span", {
                    class: "wb-dist__bar",
                    style: ce({ width: P(x.count) })
                  }, null, 4)
                ]),
                t("span", Ir, w(x.count), 1)
              ], 8, wr))), 128))
            ])) : (o(), u("div", xr, "暂无实例数据"))
          ])
        ])
      ], 64)) : M("", !0),
      t("h3", Dr, [
        _[15] || (_[15] = ee(" 最近待办 ", -1)),
        a.value > c.value.length ? (o(), u("button", {
          key: 0,
          class: "jf-btn jf-btn--ghost jf-btn--sm",
          onClick: _[0] || (_[0] = (x) => i("goto", "todo"))
        }, " 查看全部 " + w(a.value) + " 条 → ", 1)) : M("", !0)
      ]),
      s.value ? (o(), u("div", Nr, "加载中...")) : (o(), u(G, { key: 3 }, [
        c.value.length ? (o(), u("table", Tr, [
          _[16] || (_[16] = t("thead", null, [
            t("tr", null, [
              t("th", null, "流程"),
              t("th", null, "任务"),
              t("th", null, "时间"),
              t("th", null, "操作")
            ])
          ], -1)),
          t("tbody", null, [
            (o(!0), u(G, null, le(c.value, (x) => (o(), u("tr", {
              key: x.id
            }, [
              t("td", null, w(x.processDefineDisplayName || "-"), 1),
              t("td", null, [
                t("strong", null, w(x.displayName), 1)
              ]),
              t("td", Pr, w(H(xe)(x.createTime, !0)), 1),
              t("td", null, [
                t("div", Mr, [
                  t("button", {
                    class: "jf-btn jf-btn--primary jf-btn--sm",
                    onClick: (L) => fe(x.id)
                  }, "办理", 8, Er),
                  t("button", {
                    class: "jf-btn jf-btn--ghost jf-btn--sm",
                    onClick: (L) => pe(x.processInstanceId)
                  }, "详情", 8, Lr)
                ])
              ])
            ]))), 128))
          ])
        ])) : (o(), u("div", Ar, [
          _[17] || (_[17] = ee("暂无待办，喝口茶吧 ", -1)),
          J(Pe, {
            name: "coffee",
            size: 14
          })
        ]))
      ], 64)),
      J(Nn, {
        visible: V.value,
        "onUpdate:visible": _[1] || (_[1] = (x) => V.value = x),
        "task-id": F.value,
        onChanged: W
      }, null, 8, ["visible", "task-id"]),
      J(gt, {
        visible: S.value,
        "onUpdate:visible": _[2] || (_[2] = (x) => S.value = x),
        "instance-id": z.value
      }, null, 8, ["visible", "instance-id"])
    ]));
  }
}), Nc = /* @__PURE__ */ $e(Sr, [["__scopeId", "data-v-b4fea405"]]), Or = { class: "jf-page" }, zr = { class: "jf-page-title" }, Br = {
  key: 0,
  class: "jf-loading"
}, Ur = { class: "jf-group-title" }, Vr = { class: "jf-card-grid" }, Rr = ["onClick"], Fr = { class: "jf-card-icon" }, Jr = { class: "jf-card-name" }, Yr = { class: "jf-card-remark" }, Wr = {
  key: 0,
  class: "jf-card-badge"
}, Gr = {
  key: 0,
  class: "jf-empty"
}, Hr = {
  key: 0,
  class: "jf-empty"
}, Kr = /* @__PURE__ */ q({
  name: "JfApplyListPage",
  __name: "ApplyListPage",
  emits: ["goto"],
  setup(e, { emit: l }) {
    const i = l, { api: n } = je(), s = b(!1), c = b({}), a = b({}), r = b(!1), y = b(null), v = {
      approval: "审批类",
      leave: "请假类",
      expense: "报销类",
      purchase: "采购类",
      other: "其他"
    };
    function h(C) {
      return v[C] || C || "未分类";
    }
    async function p() {
      s.value = !0;
      try {
        try {
          c.value = await n.processDesign.listByType();
        } catch {
          c.value = {};
        }
        for (const D of Object.keys(c.value))
          c.value[D] = c.value[D].filter((T) => T.processDefineState !== 0);
        if (Object.keys(c.value).every((D) => !c.value[D].length)) {
          const D = await n.processDefine.page({ pageNum: 1, pageSize: 100 });
          c.value = {
            全部流程: D.rows.filter((T) => T.state !== 0).map((T) => ({
              processDesignId: T.id,
              processDefineId: T.id,
              name: T.name,
              displayName: T.displayName,
              icon: "doc",
              remark: `v${T.version}`,
              processDefineState: T.state,
              jsonObject: null
            }))
          };
        }
        f();
      } finally {
        s.value = !1;
      }
    }
    async function f() {
      try {
        const C = await n.processInstance.page({
          pageNum: 1,
          pageSize: 100,
          m_EQ_state: 10
        }), D = /* @__PURE__ */ new Map();
        for (const N of C.rows) {
          const U = String(N.processDefineId ?? "");
          if (!U) continue;
          const P = D.get(U) ?? [];
          P.push(N.id), D.set(U, P);
        }
        const T = {};
        await Promise.all([...D.entries()].map(async ([N, U]) => {
          let P = "";
          try {
            P = (await n.processInstance.getAssigneeTextData(U[0]) || []).map((V) => V.label || V.value).filter(Boolean).slice(0, 3).join("、");
          } catch {
          }
          T[N] = { count: U.length, assignee: P };
        })), a.value = T;
      } catch {
      }
    }
    function j(C) {
      if (!C.processDefineId) {
        X.error("该流程尚未发布（processDefineId 为空），无法发起");
        return;
      }
      y.value = {
        processDefineId: C.processDefineId,
        name: C.name,
        displayName: C.displayName,
        jsonObject: C.jsonObject
      }, r.value = !0;
    }
    function g() {
      i("goto", "mine");
    }
    return he(p), (C, D) => (o(), u("div", Or, [
      t("h2", zr, [
        J(Pe, {
          name: "apply",
          size: 18
        }),
        D[1] || (D[1] = ee(" 发起申请", -1))
      ]),
      s.value ? (o(), u("div", Br, "加载中...")) : (o(), u(G, { key: 1 }, [
        (o(!0), u(G, null, le(c.value, (T, N) => (o(), u("div", {
          key: N,
          class: "jf-card-group"
        }, [
          t("h3", Ur, w(h(N)), 1),
          t("div", Vr, [
            (o(!0), u(G, null, le(T, (U) => (o(), u("div", {
              key: U.processDesignId,
              class: "jf-card",
              onClick: (P) => j(U)
            }, [
              t("div", Fr, [
                J(Pe, {
                  name: U.icon || "doc",
                  size: 26
                }, null, 8, ["name"])
              ]),
              t("div", Jr, w(U.displayName || U.name), 1),
              t("div", Yr, w(U.remark || U.name), 1),
              a.value[U.processDefineId ?? ""] ? (o(), u("div", Wr, [
                ee(w(a.value[U.processDefineId ?? ""].count) + " 条在办", 1),
                a.value[U.processDefineId ?? ""].assignee ? (o(), u(G, { key: 0 }, [
                  ee(" · " + w(a.value[U.processDefineId ?? ""].assignee), 1)
                ], 64)) : M("", !0)
              ])) : M("", !0)
            ], 8, Rr))), 128))
          ]),
          T.length ? M("", !0) : (o(), u("div", Gr, "该类型暂无流程"))
        ]))), 128)),
        Object.keys(c.value).length ? M("", !0) : (o(), u("div", Hr, "暂无可用流程"))
      ], 64)),
      J(Ko, {
        visible: r.value,
        "onUpdate:visible": D[0] || (D[0] = (T) => r.value = T),
        define: y.value,
        onStarted: g
      }, null, 8, ["visible", "define"])
    ]));
  }
}), Tc = /* @__PURE__ */ $e(Kr, [["__scopeId", "data-v-21c129e5"]]), Qr = { class: "jf-page" }, Xr = { class: "jf-page-title" }, qr = {
  key: 0,
  class: "jf-loading"
}, Zr = {
  key: 0,
  class: "jf-table"
}, ed = { class: "jf-muted" }, td = { class: "jf-muted" }, nd = { class: "jf-btn-row" }, ld = ["onClick"], ad = ["onClick"], sd = {
  key: 1,
  class: "jf-empty"
}, od = {
  key: 2,
  class: "jf-pagination"
}, id = ["disabled"], rd = { class: "jf-muted" }, dd = ["disabled"], vn = 10, ud = /* @__PURE__ */ q({
  name: "JfMyInstancePage",
  __name: "MyInstancePage",
  setup(e) {
    const { api: l, can: i } = je(), n = b(!1), s = b([]), c = b(1), a = b(0), r = b(0), y = b(""), v = b(!1), h = b(null);
    async function p() {
      n.value = !0;
      try {
        const D = await l.processInstance.page({
          pageNum: c.value,
          pageSize: vn,
          ...y.value.trim() ? { m_LIKE_processDefineDisplayName: y.value.trim() } : {}
        });
        s.value = D.rows, a.value = D.recordCount, r.value = D.totalPage;
      } catch (D) {
        X.error(D.message || "加载实例列表失败");
      } finally {
        n.value = !1;
      }
    }
    function f(D) {
      c.value = D, p();
    }
    function j() {
      c.value = 1, p();
    }
    function g(D) {
      h.value = D, v.value = !0;
    }
    async function C(D) {
      if (window.confirm("确认撤回该流程？"))
        try {
          await l.processInstance.withdraw(D.id), X.success("已撤回"), p();
        } catch (T) {
          X.error(`撤回失败：${T.message}`);
        }
    }
    return he(p), (D, T) => (o(), u("div", Qr, [
      t("h2", Xr, [
        J(Pe, {
          name: "mine",
          size: 18
        }),
        T[4] || (T[4] = ee(" 我发起的流程 ", -1)),
        de(t("input", {
          "onUpdate:modelValue": T[0] || (T[0] = (N) => y.value = N),
          class: "jf-input jf-page-search",
          placeholder: "搜索流程名...",
          onKeyup: st(j, ["enter"])
        }, null, 544), [
          [Te, y.value]
        ])
      ]),
      n.value ? (o(), u("div", qr, "加载中...")) : (o(), u(G, { key: 1 }, [
        s.value.length ? (o(), u("table", Zr, [
          T[5] || (T[5] = t("thead", null, [
            t("tr", null, [
              t("th", null, "ID"),
              t("th", null, "流程"),
              t("th", null, "状态"),
              t("th", null, "时间"),
              t("th", null, "操作")
            ])
          ], -1)),
          t("tbody", null, [
            (o(!0), u(G, null, le(s.value, (N) => (o(), u("tr", {
              key: N.id
            }, [
              t("td", ed, w(N.id), 1),
              t("td", null, w(N.displayName || N.processDefineDisplayName), 1),
              t("td", null, [
                J(Oe, {
                  type: H($n)(N.state)
                }, {
                  default: te(() => [
                    ee(w(H(Yt)(N.state)), 1)
                  ]),
                  _: 2
                }, 1032, ["type"])
              ]),
              t("td", td, w(H(xe)(N.createTime, !0)), 1),
              t("td", null, [
                t("div", nd, [
                  t("button", {
                    class: "jf-btn jf-btn--ghost jf-btn--sm",
                    onClick: (U) => g(N.id)
                  }, "详情 →", 8, ld),
                  H(i)(["wf:processInstance:withdraw"]) && N.state === 10 ? (o(), u("button", {
                    key: 0,
                    class: "jf-btn jf-btn--ghost jf-btn--sm",
                    onClick: (U) => C(N)
                  }, "撤回", 8, ad)) : M("", !0)
                ])
              ])
            ]))), 128))
          ])
        ])) : (o(), u("div", sd, "暂无记录")),
        a.value > vn ? (o(), u("div", od, [
          t("button", {
            class: "jf-btn jf-btn--ghost jf-btn--sm",
            disabled: c.value <= 1,
            onClick: T[1] || (T[1] = (N) => f(c.value - 1))
          }, "上一页", 8, id),
          t("span", rd, w(c.value) + "/" + w(r.value) + "（共 " + w(a.value) + " 条）", 1),
          t("button", {
            class: "jf-btn jf-btn--ghost jf-btn--sm",
            disabled: c.value >= r.value,
            onClick: T[2] || (T[2] = (N) => f(c.value + 1))
          }, "下一页", 8, dd)
        ])) : M("", !0)
      ], 64)),
      J(gt, {
        visible: v.value,
        "onUpdate:visible": T[3] || (T[3] = (N) => v.value = N),
        "instance-id": h.value,
        onChanged: p
      }, null, 8, ["visible", "instance-id"])
    ]));
  }
}), Pc = /* @__PURE__ */ $e(ud, [["__scopeId", "data-v-a1669786"]]), cd = { class: "jf-page" }, fd = { class: "jf-page-title" }, pd = {
  key: 0,
  class: "jf-loading"
}, vd = {
  key: 0,
  class: "jf-table"
}, md = { class: "jf-muted" }, hd = { class: "jf-muted" }, yd = { class: "jf-btn-row" }, gd = ["onClick"], bd = ["onClick"], kd = {
  key: 1,
  class: "jf-empty"
}, jd = {
  key: 2,
  class: "jf-pagination"
}, $d = ["disabled"], wd = { class: "jf-muted" }, _d = ["disabled"], mn = 10, Cd = /* @__PURE__ */ q({
  name: "JfTodoPage",
  __name: "TodoPage",
  setup(e) {
    const { api: l } = je(), i = b(!1), n = b([]), s = b(1), c = b(0), a = b(0), r = b(null), y = b(""), v = b(!1), h = b(null), p = b(!1), f = b(null);
    async function j() {
      i.value = !0;
      try {
        const N = await l.processTask.todoList({
          pageNum: s.value,
          pageSize: mn,
          ...y.value.trim() ? { m_LIKE_processDefineDisplayName: y.value.trim() } : {}
        });
        n.value = N.rows, c.value = N.recordCount, a.value = N.totalPage;
      } catch (N) {
        X.error(N.message || "加载待办列表失败");
      } finally {
        i.value = !1;
      }
    }
    function g(N) {
      s.value = N, j();
    }
    function C() {
      s.value = 1, j();
    }
    function D(N) {
      h.value = N, v.value = !0;
    }
    function T(N) {
      f.value = N, p.value = !0;
    }
    return he(j), (N, U) => (o(), u("div", cd, [
      t("h2", fd, [
        J(Pe, {
          name: "todo",
          size: 18
        }),
        U[5] || (U[5] = ee(" 我的待办 ", -1)),
        de(t("input", {
          "onUpdate:modelValue": U[0] || (U[0] = (P) => y.value = P),
          class: "jf-input jf-page-search",
          placeholder: "搜索流程名...",
          onKeyup: st(C, ["enter"])
        }, null, 544), [
          [Te, y.value]
        ])
      ]),
      i.value ? (o(), u("div", pd, "加载中...")) : (o(), u(G, { key: 1 }, [
        n.value.length ? (o(), u("table", vd, [
          U[6] || (U[6] = t("thead", null, [
            t("tr", null, [
              t("th", null, "流程"),
              t("th", null, "任务"),
              t("th", null, "表单"),
              t("th", null, "时间"),
              t("th", null, "操作")
            ])
          ], -1)),
          t("tbody", null, [
            (o(!0), u(G, null, le(n.value, (P) => (o(), u("tr", {
              key: P.id,
              class: ne({ "jf-row-flash": r.value === P.id })
            }, [
              t("td", null, w(P.processDefineDisplayName || "-"), 1),
              t("td", null, [
                t("strong", null, w(P.displayName), 1)
              ]),
              t("td", md, w(P.formKey || "-"), 1),
              t("td", hd, w(H(xe)(P.createTime, !0)), 1),
              t("td", null, [
                t("div", yd, [
                  t("button", {
                    class: "jf-btn jf-btn--primary jf-btn--sm",
                    onClick: (B) => D(P.id)
                  }, "办理", 8, gd),
                  t("button", {
                    class: "jf-btn jf-btn--ghost jf-btn--sm",
                    onClick: (B) => T(P.processInstanceId)
                  }, "详情", 8, bd)
                ])
              ])
            ], 2))), 128))
          ])
        ])) : (o(), u("div", kd, "暂无待办")),
        c.value > mn ? (o(), u("div", jd, [
          t("button", {
            class: "jf-btn jf-btn--ghost jf-btn--sm",
            disabled: s.value <= 1,
            onClick: U[1] || (U[1] = (P) => g(s.value - 1))
          }, "上一页", 8, $d),
          t("span", wd, w(s.value) + "/" + w(a.value) + "（共 " + w(c.value) + " 条）", 1),
          t("button", {
            class: "jf-btn jf-btn--ghost jf-btn--sm",
            disabled: s.value >= a.value,
            onClick: U[2] || (U[2] = (P) => g(s.value + 1))
          }, "下一页", 8, _d)
        ])) : M("", !0)
      ], 64)),
      J(Nn, {
        visible: v.value,
        "onUpdate:visible": U[3] || (U[3] = (P) => v.value = P),
        "task-id": h.value,
        onChanged: j
      }, null, 8, ["visible", "task-id"]),
      J(gt, {
        visible: p.value,
        "onUpdate:visible": U[4] || (U[4] = (P) => p.value = P),
        "instance-id": f.value,
        onChanged: j
      }, null, 8, ["visible", "instance-id"])
    ]));
  }
}), Mc = /* @__PURE__ */ $e(Cd, [["__scopeId", "data-v-0e29dadb"]]), Id = { class: "jf-page" }, xd = { class: "jf-page-title" }, Dd = {
  key: 0,
  class: "jf-loading"
}, Nd = {
  key: 0,
  class: "jf-table"
}, Td = { class: "jf-muted" }, Pd = ["onClick"], Md = {
  key: 1,
  class: "jf-empty"
}, Ed = {
  key: 2,
  class: "jf-pagination"
}, Ld = ["disabled"], Ad = { class: "jf-muted" }, Sd = ["disabled"], hn = 10, Od = /* @__PURE__ */ q({
  name: "JfDonePage",
  __name: "DonePage",
  setup(e) {
    const { api: l } = je(), i = b(!1), n = b([]), s = b(1), c = b(0), a = b(0), r = b(""), y = b(!1), v = b(null);
    async function h() {
      i.value = !0;
      try {
        const g = await l.processTask.doneList({
          pageNum: s.value,
          pageSize: hn,
          ...r.value.trim() ? { m_LIKE_processDefineDisplayName: r.value.trim() } : {}
        });
        n.value = g.rows, c.value = g.recordCount, a.value = g.totalPage;
      } catch (g) {
        X.error(g.message || "加载已办列表失败");
      } finally {
        i.value = !1;
      }
    }
    function p(g) {
      s.value = g, h();
    }
    function f() {
      s.value = 1, h();
    }
    function j(g) {
      v.value = g, y.value = !0;
    }
    return he(h), (g, C) => (o(), u("div", Id, [
      t("h2", xd, [
        J(Pe, {
          name: "done",
          size: 18
        }),
        C[4] || (C[4] = ee(" 我的已办 ", -1)),
        de(t("input", {
          "onUpdate:modelValue": C[0] || (C[0] = (D) => r.value = D),
          class: "jf-input jf-page-search",
          placeholder: "搜索流程名...",
          onKeyup: st(f, ["enter"])
        }, null, 544), [
          [Te, r.value]
        ])
      ]),
      i.value ? (o(), u("div", Dd, "加载中...")) : (o(), u(G, { key: 1 }, [
        n.value.length ? (o(), u("table", Nd, [
          C[5] || (C[5] = t("thead", null, [
            t("tr", null, [
              t("th", null, "流程"),
              t("th", null, "任务"),
              t("th", null, "状态"),
              t("th", null, "完成时间"),
              t("th", null, "操作")
            ])
          ], -1)),
          t("tbody", null, [
            (o(!0), u(G, null, le(n.value, (D) => (o(), u("tr", {
              key: D.id
            }, [
              t("td", null, w(D.processDefineDisplayName || "-"), 1),
              t("td", null, [
                t("strong", null, w(D.displayName), 1)
              ]),
              t("td", null, [
                J(Oe, {
                  type: H(wn)(D.taskState)
                }, {
                  default: te(() => [
                    ee(w(H(ol)(D.taskState)), 1)
                  ]),
                  _: 2
                }, 1032, ["type"])
              ]),
              t("td", Td, w(H(xe)(D.finishTime || D.createTime, !0)), 1),
              t("td", null, [
                t("button", {
                  class: "jf-btn jf-btn--ghost jf-btn--sm",
                  onClick: (T) => j(D.processInstanceId)
                }, "详情", 8, Pd)
              ])
            ]))), 128))
          ])
        ])) : (o(), u("div", Md, "暂无已办")),
        c.value > hn ? (o(), u("div", Ed, [
          t("button", {
            class: "jf-btn jf-btn--ghost jf-btn--sm",
            disabled: s.value <= 1,
            onClick: C[1] || (C[1] = (D) => p(s.value - 1))
          }, "上一页", 8, Ld),
          t("span", Ad, w(s.value) + "/" + w(a.value) + "（共 " + w(c.value) + " 条）", 1),
          t("button", {
            class: "jf-btn jf-btn--ghost jf-btn--sm",
            disabled: s.value >= a.value,
            onClick: C[2] || (C[2] = (D) => p(s.value + 1))
          }, "下一页", 8, Sd)
        ])) : M("", !0)
      ], 64)),
      J(gt, {
        visible: y.value,
        "onUpdate:visible": C[3] || (C[3] = (D) => y.value = D),
        "instance-id": v.value
      }, null, 8, ["visible", "instance-id"])
    ]));
  }
}), Ec = /* @__PURE__ */ $e(Od, [["__scopeId", "data-v-1874639e"]]), zd = { class: "jf-page" }, Bd = { class: "jf-page-title" }, Ud = {
  key: 0,
  class: "jf-loading"
}, Vd = {
  key: 0,
  class: "jf-table"
}, Rd = { class: "jf-muted" }, Fd = { class: "jf-btn-row" }, Jd = ["onClick"], Yd = ["onClick"], Wd = {
  key: 1,
  class: "jf-empty"
}, Gd = {
  key: 2,
  class: "jf-pagination"
}, Hd = ["disabled"], Kd = { class: "jf-muted" }, Qd = ["disabled"], Xd = { class: "jf-form-item" }, qd = { class: "jf-drawer-actions" }, Zd = ["disabled"], yn = 10, eu = /* @__PURE__ */ q({
  name: "JfCcListPage",
  __name: "CcListPage",
  setup(e) {
    const { api: l, can: i } = je(), n = b(!1), s = b([]), c = b(1), a = b(0), r = b(0), y = b(""), v = Ue(/* @__PURE__ */ new Set()), h = b(!1), p = b(null), f = b(!1), j = b(null), g = b([]), C = b(!1);
    async function D() {
      n.value = !0;
      try {
        const V = await l.processInstance.ccList({
          pageNum: c.value,
          pageSize: yn,
          ...y.value.trim() ? { m_LIKE_processDefineDisplayName: y.value.trim() } : {}
        });
        s.value = V.rows, a.value = V.recordCount, r.value = V.totalPage;
      } catch (V) {
        X.error(V.message || "加载抄送列表失败");
      } finally {
        n.value = !1;
      }
    }
    function T(V) {
      c.value = V, D();
    }
    function N() {
      c.value = 1, D();
    }
    async function U(V) {
      try {
        await l.processInstance.updateCCStatus(V), v.add(V);
      } catch {
      }
      p.value = V, h.value = !0;
    }
    function P(V) {
      j.value = V, g.value = [], f.value = !0;
    }
    async function B() {
      if (!(!j.value || !g.value.length)) {
        C.value = !0;
        try {
          await l.processInstance.createCCInstance(j.value, g.value), X.success("抄送成功"), f.value = !1, g.value = [];
        } catch (V) {
          X.error(V.message || "抄送失败");
        } finally {
          C.value = !1;
        }
      }
    }
    return he(D), (V, F) => (o(), u("div", zd, [
      t("h2", Bd, [
        J(Pe, {
          name: "cc",
          size: 18
        }),
        F[7] || (F[7] = ee(" 我的抄送 ", -1)),
        de(t("input", {
          "onUpdate:modelValue": F[0] || (F[0] = (S) => y.value = S),
          class: "jf-input jf-page-search",
          placeholder: "搜索流程名...",
          onKeyup: st(N, ["enter"])
        }, null, 544), [
          [Te, y.value]
        ])
      ]),
      n.value ? (o(), u("div", Ud, "加载中...")) : (o(), u(G, { key: 1 }, [
        s.value.length ? (o(), u("table", Vd, [
          F[8] || (F[8] = t("thead", null, [
            t("tr", null, [
              t("th", null, "流程"),
              t("th", null, "实例状态"),
              t("th", null, "阅读状态"),
              t("th", null, "发起人"),
              t("th", null, "时间"),
              t("th", null, "操作")
            ])
          ], -1)),
          t("tbody", null, [
            (o(!0), u(G, null, le(s.value, (S) => (o(), u("tr", {
              key: S.id
            }, [
              t("td", null, w(S.displayName || S.processDefineDisplayName), 1),
              t("td", null, [
                J(Oe, {
                  type: H($n)(S.state)
                }, {
                  default: te(() => [
                    ee(w(H(Yt)(S.state)), 1)
                  ]),
                  _: 2
                }, 1032, ["type"])
              ]),
              t("td", null, [
                J(Oe, {
                  type: v.has(S.id) ? "done" : "doing"
                }, {
                  default: te(() => [
                    ee(w(v.has(S.id) ? "已读" : "未读"), 1)
                  ]),
                  _: 2
                }, 1032, ["type"])
              ]),
              t("td", null, w(S.operator || "-"), 1),
              t("td", Rd, w(H(xe)(S.createTime, !0)), 1),
              t("td", null, [
                t("div", Fd, [
                  t("button", {
                    class: "jf-btn jf-btn--ghost jf-btn--sm",
                    onClick: (z) => U(S.id)
                  }, "详情", 8, Jd),
                  H(i)(["wf:processInstance:createCCInstance"]) ? (o(), u("button", {
                    key: 0,
                    class: "jf-btn jf-btn--ghost jf-btn--sm",
                    onClick: (z) => P(S.id)
                  }, "抄送他人", 8, Yd)) : M("", !0)
                ])
              ])
            ]))), 128))
          ])
        ])) : (o(), u("div", Wd, "暂无抄送")),
        a.value > yn ? (o(), u("div", Gd, [
          t("button", {
            class: "jf-btn jf-btn--ghost jf-btn--sm",
            disabled: c.value <= 1,
            onClick: F[1] || (F[1] = (S) => T(c.value - 1))
          }, "上一页", 8, Hd),
          t("span", Kd, w(c.value) + "/" + w(r.value) + "（共 " + w(a.value) + " 条）", 1),
          t("button", {
            class: "jf-btn jf-btn--ghost jf-btn--sm",
            disabled: c.value >= r.value,
            onClick: F[2] || (F[2] = (S) => T(c.value + 1))
          }, "下一页", 8, Qd)
        ])) : M("", !0)
      ], 64)),
      J(gt, {
        visible: h.value,
        "onUpdate:visible": F[3] || (F[3] = (S) => h.value = S),
        "instance-id": p.value,
        onChanged: D
      }, null, 8, ["visible", "instance-id"]),
      J(Ve, {
        visible: f.value,
        "onUpdate:visible": F[6] || (F[6] = (S) => f.value = S),
        title: "手动抄送",
        width: "480px"
      }, {
        default: te(() => [
          t("div", Xd, [
            F[9] || (F[9] = t("label", { class: "jf-form-label" }, "抄送人", -1)),
            J(at, {
              modelValue: g.value,
              "onUpdate:modelValue": F[4] || (F[4] = (S) => g.value = S),
              scene: "cc",
              placeholder: "搜索姓名/工号"
            }, null, 8, ["modelValue"])
          ]),
          t("div", qd, [
            t("button", {
              class: "jf-btn jf-btn--ghost",
              onClick: F[5] || (F[5] = (S) => f.value = !1)
            }, "取消"),
            t("button", {
              class: "jf-btn jf-btn--primary",
              disabled: C.value || !g.value.length,
              onClick: B
            }, "确定", 8, Zd)
          ])
        ]),
        _: 1
      }, 8, ["visible"])
    ]));
  }
}), Lc = /* @__PURE__ */ $e(eu, [["__scopeId", "data-v-e5daf096"]]), tu = { class: "jf-page" }, nu = { class: "jf-page-title" }, lu = {
  key: 0,
  class: "jf-loading"
}, au = {
  key: 0,
  class: "jf-table"
}, su = { class: "jf-muted" }, ou = { class: "jf-muted" }, iu = { class: "jf-muted" }, ru = { class: "jf-muted" }, du = { class: "jf-btn-row" }, uu = ["onClick"], cu = ["onClick"], fu = ["onClick"], pu = {
  key: 1,
  class: "jf-empty"
}, vu = {
  key: 2,
  class: "jf-pagination"
}, mu = ["disabled"], hu = { class: "jf-muted" }, yu = ["disabled"], gu = {
  key: 0,
  class: "jf-detail-body"
}, bu = { class: "jf-define-meta" }, ku = { class: "jf-define-meta-item" }, ju = { class: "jf-define-meta-item" }, $u = { class: "jf-define-meta-item" }, wu = { class: "jf-define-meta-item" }, _u = { class: "jf-define-meta-item" }, Cu = { class: "jf-define-meta-item" }, Iu = { class: "jf-define-meta-item" }, xu = {
  key: 0,
  class: "jf-detail-graph"
}, Du = {
  key: 1,
  class: "jf-empty"
}, gn = 10, Nu = /* @__PURE__ */ q({
  name: "JfProcessDefinePage",
  __name: "ProcessDefinePage",
  setup(e) {
    const { api: l, can: i } = je(), n = b(!1), s = b([]), c = b(1), a = b(0), r = b(0), y = b(""), v = b(!1), h = b(null);
    async function p() {
      n.value = !0;
      try {
        const T = await l.processDefine.page({
          pageNum: c.value,
          pageSize: gn,
          orderBy: "t.update_time desc",
          ...y.value.trim() ? { m_LIKE_displayName: y.value.trim() } : {}
        });
        s.value = T.rows, a.value = T.recordCount, r.value = T.totalPage;
      } catch (T) {
        X.error(`加载失败：${T.message}`);
      } finally {
        n.value = !1;
      }
    }
    function f() {
      c.value = 1, p();
    }
    function j(T) {
      c.value = T, p();
    }
    async function g(T) {
      try {
        h.value = await l.processDefine.detail(T.id), v.value = !0;
      } catch (N) {
        X.error(`打开详情失败：${N.message}`);
      }
    }
    async function C(T) {
      try {
        await l.processDefine.upAndDown(T.id, T.state === 1 ? 0 : 1), X.success(T.state === 1 ? "已停用" : "已启用"), p();
      } catch (N) {
        X.error(`操作失败：${N.message}`);
      }
    }
    async function D(T) {
      if (window.confirm(`确认删除流程定义「${T.displayName}」？`))
        try {
          await l.processDefine.remove(T.id), X.success("已删除"), p();
        } catch (N) {
          X.error(`删除失败：${N.message}`);
        }
    }
    return he(p), (T, N) => {
      var U;
      return o(), u("div", tu, [
        t("h2", nu, [
          J(Pe, {
            name: "define",
            size: 18
          }),
          N[4] || (N[4] = ee(" 流程定义 ", -1)),
          de(t("input", {
            "onUpdate:modelValue": N[0] || (N[0] = (P) => y.value = P),
            class: "jf-input jf-page-search",
            placeholder: "搜索编码/显示名...",
            onKeyup: st(f, ["enter"])
          }, null, 544), [
            [Te, y.value]
          ])
        ]),
        n.value ? (o(), u("div", lu, "加载中...")) : (o(), u(G, { key: 1 }, [
          s.value.length ? (o(), u("table", au, [
            N[5] || (N[5] = t("thead", null, [
              t("tr", null, [
                t("th", null, "编码"),
                t("th", null, "显示名"),
                t("th", null, "类型"),
                t("th", null, "版本"),
                t("th", null, "状态"),
                t("th", null, "更新时间"),
                t("th", null, "操作")
              ])
            ], -1)),
            t("tbody", null, [
              (o(!0), u(G, null, le(s.value, (P) => (o(), u("tr", {
                key: P.id
              }, [
                t("td", su, w(P.name), 1),
                t("td", null, [
                  t("strong", null, w(P.displayName), 1)
                ]),
                t("td", ou, w(P.type), 1),
                t("td", iu, "v" + w(P.version), 1),
                t("td", null, [
                  J(Oe, {
                    type: P.state === 1 ? "done" : "info"
                  }, {
                    default: te(() => [
                      ee(w(P.state === 1 ? "启用" : "停用"), 1)
                    ]),
                    _: 2
                  }, 1032, ["type"])
                ]),
                t("td", ru, w(H(xe)(P.updateTime || P.createTime, !0)), 1),
                t("td", null, [
                  t("div", du, [
                    t("button", {
                      class: "jf-btn jf-btn--ghost jf-btn--sm",
                      onClick: (B) => g(P)
                    }, "详情", 8, uu),
                    H(i)(["wf:processDefine:upAndDown"]) ? (o(), u("button", {
                      key: 0,
                      class: "jf-btn jf-btn--ghost jf-btn--sm",
                      onClick: (B) => C(P)
                    }, w(P.state === 1 ? "停用" : "启用"), 9, cu)) : M("", !0),
                    H(i)(["wf:processDefine:remove"]) ? (o(), u("button", {
                      key: 1,
                      class: "jf-btn jf-btn--danger jf-btn--sm",
                      onClick: (B) => D(P)
                    }, "删除", 8, fu)) : M("", !0)
                  ])
                ])
              ]))), 128))
            ])
          ])) : (o(), u("div", pu, "暂无流程定义（先在设计页发布）")),
          a.value > gn ? (o(), u("div", vu, [
            t("button", {
              class: "jf-btn jf-btn--ghost jf-btn--sm",
              disabled: c.value <= 1,
              onClick: N[1] || (N[1] = (P) => j(c.value - 1))
            }, "上一页", 8, mu),
            t("span", hu, w(c.value) + "/" + w(r.value) + "（共 " + w(a.value) + " 条）", 1),
            t("button", {
              class: "jf-btn jf-btn--ghost jf-btn--sm",
              disabled: c.value >= r.value,
              onClick: N[2] || (N[2] = (P) => j(c.value + 1))
            }, "下一页", 8, yu)
          ])) : M("", !0)
        ], 64)),
        J(Ve, {
          visible: v.value,
          "onUpdate:visible": N[3] || (N[3] = (P) => v.value = P),
          title: ((U = h.value) == null ? void 0 : U.displayName) || "流程详情",
          width: "820px",
          fill: ""
        }, {
          default: te(() => [
            h.value ? (o(), u("div", gu, [
              t("div", bu, [
                t("div", ku, [
                  N[6] || (N[6] = t("span", { class: "jf-muted" }, "编码", -1)),
                  t("strong", null, w(h.value.name), 1)
                ]),
                t("div", ju, [
                  N[7] || (N[7] = t("span", { class: "jf-muted" }, "显示名", -1)),
                  t("strong", null, w(h.value.displayName), 1)
                ]),
                t("div", $u, [
                  N[8] || (N[8] = t("span", { class: "jf-muted" }, "类型", -1)),
                  t("span", null, w(h.value.type || "-"), 1)
                ]),
                t("div", wu, [
                  N[9] || (N[9] = t("span", { class: "jf-muted" }, "版本", -1)),
                  t("span", null, "v" + w(h.value.version), 1)
                ]),
                t("div", _u, [
                  N[10] || (N[10] = t("span", { class: "jf-muted" }, "状态", -1)),
                  J(Oe, {
                    type: h.value.state === 1 ? "done" : "info"
                  }, {
                    default: te(() => [
                      ee(w(h.value.state === 1 ? "启用" : "停用"), 1)
                    ]),
                    _: 1
                  }, 8, ["type"])
                ]),
                t("div", Cu, [
                  N[11] || (N[11] = t("span", { class: "jf-muted" }, "创建", -1)),
                  t("span", null, w(H(xe)(h.value.createTime, !0)) + w(h.value.createUser ? `（${h.value.createUser}）` : ""), 1)
                ]),
                t("div", Iu, [
                  N[12] || (N[12] = t("span", { class: "jf-muted" }, "更新", -1)),
                  t("span", null, w(H(xe)(h.value.updateTime || h.value.createTime, !0)), 1)
                ])
              ]),
              h.value.jsonObject ? (o(), u("div", xu, [
                J(Lt, {
                  "graph-data": h.value.jsonObject
                }, null, 8, ["graph-data"])
              ])) : (o(), u("div", Du, "该定义无流程图（content 缺失）"))
            ])) : M("", !0)
          ]),
          _: 1
        }, 8, ["visible", "title"])
      ]);
    };
  }
}), Ac = /* @__PURE__ */ $e(Nu, [["__scopeId", "data-v-8fbe4d7c"]]), Tu = { class: "jf-page-title" }, Pu = {
  key: 0,
  class: "jf-loading"
}, Mu = {
  key: 1,
  class: "jf-empty"
}, Eu = {
  key: 0,
  class: "jf-table"
}, Lu = { class: "jf-muted" }, Au = { class: "jf-muted" }, Su = { class: "jf-muted" }, Ou = { class: "jf-btn-row" }, zu = ["onClick"], Bu = ["onClick"], Uu = ["onClick"], Vu = {
  key: 1,
  class: "jf-empty"
}, Ru = {
  key: 2,
  class: "jf-pagination"
}, Fu = ["disabled"], Ju = { class: "jf-muted" }, Yu = ["disabled"], Wu = {
  key: 1,
  class: "jf-designer-wrap"
}, Gu = { class: "jf-designer-bar" }, Hu = {
  class: "jf-muted",
  style: { "font-size": "13px" }
}, Ku = ["disabled"], Qu = ["disabled"], Xu = { class: "jf-designer-body" }, bn = 10, qu = /* @__PURE__ */ q({
  name: "JfProcessDesignPage",
  __name: "ProcessDesignPage",
  setup(e) {
    const { api: l, can: i } = je(), n = b(!1), s = b(""), c = b([]), a = b(1), r = b(0), y = b(0), v = b(""), h = b(!1), p = b(null), f = b(""), j = b(""), g = b(null), C = b(!1), D = b(null);
    function T() {
      var $;
      ($ = D.value) == null || $.click();
    }
    async function N($) {
      var x;
      const _ = (x = $.target.files) == null ? void 0 : x[0];
      if ($.target.value = "", !!_)
        try {
          const L = JSON.parse(await _.text());
          if (!L || typeof L != "object") throw new Error("不是有效的流程 JSON");
          p.value = { id: "", name: L.name || "", displayName: L.displayName || "", type: L.type || "approval", isDeployed: 0, jsonObject: L }, f.value = L.name || "imported", j.value = L.displayName || "导入流程", g.value = L, h.value = !0, X.success("已导入设计稿，请保存并发布");
        } catch (L) {
          X.error(L.message || "导入失败");
        }
    }
    async function U() {
      n.value = !0, s.value = "";
      try {
        const $ = await l.processDesign.page({
          pageNum: a.value,
          pageSize: bn,
          orderBy: "t.update_time desc",
          ...v.value.trim() ? { m_LIKE_displayName: v.value.trim() } : {}
        });
        c.value = $.rows, r.value = $.recordCount, y.value = $.totalPage;
      } catch ($) {
        s.value = `流程设计功能不可用：${$.message}（后端需注册扩展仓储）`;
      } finally {
        n.value = !1;
      }
    }
    function P($) {
      a.value = $, U();
    }
    function B() {
      a.value = 1, U();
    }
    async function V() {
      p.value = { id: "", name: "", displayName: "", type: "approval", isDeployed: 0, jsonObject: null }, f.value = "", j.value = "", g.value = null, h.value = !0;
    }
    async function F($) {
      const _ = await l.processDesign.detail($.id);
      p.value = { ...$, jsonObject: _.jsonObject }, f.value = $.name, j.value = $.displayName, g.value = _.jsonObject ? { ..._.jsonObject } : null, h.value = !0;
    }
    async function S($) {
      const _ = $.isDeployed === 1;
      if (window.confirm(`确认${_ ? "重新" : ""}发布设计「${$.displayName}」？（${_ ? "已部署流程改版重发布" : "生成流程定义，版本+1"}）`))
        try {
          _ ? await l.processDesign.redeploy($.id) : await l.processDesign.deploy($.id), X.success(_ ? "重新发布成功" : "发布成功"), U();
        } catch (x) {
          X.error(x.message || "发布失败");
        }
    }
    async function z($) {
      if (window.confirm(`确认删除设计「${$.displayName}」？`))
        try {
          await l.processDesign.remove($.id), X.success("已删除"), U();
        } catch (_) {
          X.error(_.message || "删除失败");
        }
    }
    async function W($) {
      var _, x;
      C.value = !0;
      try {
        if ((_ = p.value) != null && _.id)
          await l.processDesign.update(p.value.id, {
            name: f.value,
            displayName: j.value
          });
        else {
          const L = await l.processDesign.save({
            name: f.value || ($ == null ? void 0 : $.name) || "new-flow",
            displayName: j.value || ($ == null ? void 0 : $.displayName) || "新流程",
            type: ($ == null ? void 0 : $.type) || "approval"
          });
          p.value = { ...p.value, id: L.id, isDeployed: 0 };
        }
        await l.processDesign.updateDefine(p.value.id, {
          ...$,
          name: f.value || ($ == null ? void 0 : $.name),
          displayName: j.value || ($ == null ? void 0 : $.displayName),
          type: ($ == null ? void 0 : $.type) || ((x = p.value) == null ? void 0 : x.type) || "approval"
        }), U();
      } finally {
        C.value = !1;
      }
    }
    async function fe() {
      var $;
      if (g.value)
        await W(g.value);
      else {
        C.value = !0;
        try {
          if (($ = p.value) != null && $.id)
            await l.processDesign.update(p.value.id, {
              name: f.value,
              displayName: j.value
            });
          else {
            const _ = await l.processDesign.save({
              name: f.value || "new-flow",
              displayName: j.value || "新流程",
              type: "approval"
            });
            p.value = { ...p.value, id: _.id, isDeployed: 0 };
          }
          U();
        } finally {
          C.value = !1;
        }
      }
    }
    async function pe() {
      var $;
      if (await fe(), ($ = p.value) != null && $.id)
        try {
          await l.processDesign.deploy(p.value.id), X.success("发布成功"), U();
        } catch (_) {
          X.error(_.message || "发布失败");
        }
    }
    return he(U), ($, _) => {
      var x;
      return o(), u("div", {
        class: ne(["jf-page jf-page--full", { "jf-page--designing": h.value }])
      }, [
        t("h2", Tu, [
          J(Pe, {
            name: "design",
            size: 18
          }),
          _[7] || (_[7] = ee(" 流程设计 ", -1)),
          de(t("input", {
            "onUpdate:modelValue": _[0] || (_[0] = (L) => v.value = L),
            class: "jf-input jf-page-search",
            placeholder: "搜索编码/显示名...",
            onKeyup: st(B, ["enter"])
          }, null, 544), [
            [Te, v.value]
          ]),
          H(i)(["wf:processDesign:save"]) ? (o(), u("button", {
            key: 0,
            class: "jf-btn jf-btn--primary jf-btn--sm",
            onClick: V
          }, "＋ 新建流程")) : M("", !0),
          H(i)(["wf:processDesign:save"]) ? (o(), u("button", {
            key: 1,
            class: "jf-btn jf-btn--ghost jf-btn--sm",
            title: "导入 LogicFlow JSON（演示稿：/showcase-leave.json）",
            onClick: T
          }, "导入 JSON")) : M("", !0),
          t("input", {
            ref_key: "importInput",
            ref: D,
            type: "file",
            accept: "application/json",
            style: { display: "none" },
            onChange: N
          }, null, 544)
        ]),
        h.value ? (o(), u("div", Wu, [
          t("div", Gu, [
            de(t("input", {
              "onUpdate:modelValue": _[3] || (_[3] = (L) => f.value = L),
              class: "jf-input",
              placeholder: "流程编码（唯一，如 leave）",
              style: { width: "200px" }
            }, null, 512), [
              [Te, f.value]
            ]),
            de(t("input", {
              "onUpdate:modelValue": _[4] || (_[4] = (L) => j.value = L),
              class: "jf-input",
              placeholder: "显示名（如 请假审批）",
              style: { width: "200px" }
            }, null, 512), [
              [Te, j.value]
            ]),
            t("span", Hu, w(((x = p.value) == null ? void 0 : x.isDeployed) === 1 ? "（已发布，改动后需重新发布）" : "（未发布）"), 1),
            _[9] || (_[9] = t("div", { style: { flex: "1" } }, null, -1)),
            t("button", {
              class: "jf-btn jf-btn--ghost",
              onClick: _[5] || (_[5] = (L) => {
                h.value = !1, U();
              })
            }, "返回列表"),
            t("button", {
              class: "jf-btn jf-btn--ghost",
              disabled: C.value,
              onClick: fe
            }, "保存草稿", 8, Ku),
            t("button", {
              class: "jf-btn jf-btn--primary",
              disabled: C.value,
              onClick: pe
            }, "保存并发布", 8, Qu)
          ]),
          t("div", Xu, [
            h.value ? (o(), ae(H(Pt), {
              key: 0,
              value: g.value,
              "onUpdate:value": _[6] || (_[6] = (L) => g.value = L),
              mode: "dingtalk",
              onOnSave: W
            }, null, 8, ["value"])) : M("", !0)
          ])
        ])) : (o(), u(G, { key: 0 }, [
          n.value ? (o(), u("div", Pu, "加载中...")) : s.value ? (o(), u("div", Mu, w(s.value), 1)) : (o(), u(G, { key: 2 }, [
            c.value.length ? (o(), u("table", Eu, [
              _[8] || (_[8] = t("thead", null, [
                t("tr", null, [
                  t("th", null, "编码"),
                  t("th", null, "显示名"),
                  t("th", null, "类型"),
                  t("th", null, "部署"),
                  t("th", null, "更新时间"),
                  t("th", null, "操作")
                ])
              ], -1)),
              t("tbody", null, [
                (o(!0), u(G, null, le(c.value, (L) => (o(), u("tr", {
                  key: L.id
                }, [
                  t("td", Lu, w(L.name), 1),
                  t("td", null, [
                    t("strong", null, w(L.displayName), 1)
                  ]),
                  t("td", Au, w(L.type), 1),
                  t("td", null, [
                    J(Oe, {
                      type: L.isDeployed === 1 ? "done" : "info"
                    }, {
                      default: te(() => [
                        ee(w(L.isDeployed === 1 ? "已部署" : "未部署"), 1)
                      ]),
                      _: 2
                    }, 1032, ["type"])
                  ]),
                  t("td", Su, w(H(xe)(L.updateTime || L.createTime, !0)), 1),
                  t("td", null, [
                    t("div", Ou, [
                      t("button", {
                        class: "jf-btn jf-btn--ghost jf-btn--sm",
                        onClick: (ie) => F(L)
                      }, "编辑", 8, zu),
                      H(i)(["wf:processDesign:deploy"]) ? (o(), u("button", {
                        key: 0,
                        class: "jf-btn jf-btn--primary jf-btn--sm",
                        onClick: (ie) => S(L)
                      }, w(L.isDeployed === 1 ? "重新发布" : "发布"), 9, Bu)) : M("", !0),
                      H(i)(["wf:processDesign:remove"]) ? (o(), u("button", {
                        key: 1,
                        class: "jf-btn jf-btn--danger jf-btn--sm",
                        onClick: (ie) => z(L)
                      }, "删除", 8, Uu)) : M("", !0)
                    ])
                  ])
                ]))), 128))
              ])
            ])) : (o(), u("div", Vu, "暂无流程设计")),
            r.value > bn ? (o(), u("div", Ru, [
              t("button", {
                class: "jf-btn jf-btn--ghost jf-btn--sm",
                disabled: a.value <= 1,
                onClick: _[1] || (_[1] = (L) => P(a.value - 1))
              }, "上一页", 8, Fu),
              t("span", Ju, w(a.value) + "/" + w(y.value) + "（共 " + w(r.value) + " 条）", 1),
              t("button", {
                class: "jf-btn jf-btn--ghost jf-btn--sm",
                disabled: a.value >= y.value,
                onClick: _[2] || (_[2] = (L) => P(a.value + 1))
              }, "下一页", 8, Yu)
            ])) : M("", !0)
          ], 64))
        ], 64))
      ], 2);
    };
  }
}), Sc = /* @__PURE__ */ $e(qu, [["__scopeId", "data-v-b2cb8a23"]]), Zu = { class: "jf-page" }, ec = { class: "jf-page-title" }, tc = {
  key: 0,
  class: "jf-loading"
}, nc = {
  key: 1,
  class: "jf-empty"
}, lc = {
  key: 0,
  class: "jf-table"
}, ac = { class: "jf-muted" }, sc = { class: "jf-btn-row" }, oc = ["onClick"], ic = ["onClick"], rc = ["onClick"], dc = {
  key: 1,
  class: "jf-empty"
}, uc = {
  key: 2,
  class: "jf-pagination"
}, cc = ["disabled"], fc = { class: "jf-muted" }, pc = ["disabled"], vc = { class: "jf-form-item" }, mc = { class: "jf-form-item" }, hc = { class: "jf-form-row" }, yc = { class: "jf-form-item" }, gc = { class: "jf-form-item" }, bc = { class: "jf-form-item" }, kc = { class: "jf-drawer-actions" }, jc = ["disabled"], kn = 10, Oc = /* @__PURE__ */ q({
  name: "JfSurrogatePage",
  __name: "SurrogatePage",
  setup(e) {
    const { api: l, can: i } = je(), n = b(!1), s = b(""), c = b([]), a = b(1), r = b(0), y = b(0), v = b(!1), h = b(null), p = b({}), f = b(!1), j = E({
      get: () => p.value.surrogate ? [p.value.surrogate] : [],
      set: (P) => {
        p.value.surrogate = P[0] ?? "";
      }
    });
    async function g() {
      n.value = !0, s.value = "";
      try {
        const P = await l.processSurrogate.page({ pageNum: a.value, pageSize: kn });
        c.value = P.rows, r.value = P.recordCount, y.value = P.totalPage;
      } catch (P) {
        s.value = `委托功能不可用：${P.message}（后端需注册扩展仓储）`;
      } finally {
        n.value = !1;
      }
    }
    function C(P) {
      a.value = P, g();
    }
    function D(P) {
      h.value = (P == null ? void 0 : P.id) ?? null, p.value = {
        processName: (P == null ? void 0 : P.processName) ?? "",
        surrogate: (P == null ? void 0 : P.surrogate) ?? "",
        startTime: P != null && P.startTime ? P.startTime.slice(0, 16) : "",
        endTime: P != null && P.endTime ? P.endTime.slice(0, 16) : "",
        enabled: (P == null ? void 0 : P.enabled) ?? 1
      }, v.value = !0;
    }
    async function T() {
      if (!p.value.surrogate || !p.value.startTime || !p.value.endTime) {
        X.error("被委托人/生效时间/失效时间必填");
        return;
      }
      f.value = !0;
      try {
        const P = {
          ...p.value,
          startTime: p.value.startTime ? p.value.startTime.replace("T", " ") + ":00" : null,
          endTime: p.value.endTime ? p.value.endTime.replace("T", " ") + ":00" : null
        };
        h.value && (P.id = h.value), await l.processSurrogate.save(P), X.success("已保存"), v.value = !1, g();
      } catch (P) {
        X.error(`保存失败：${P.message}`);
      } finally {
        f.value = !1;
      }
    }
    async function N(P) {
      try {
        await l.processSurrogate.save({
          id: P.id,
          processName: P.processName ?? "",
          surrogate: P.surrogate,
          startTime: P.startTime,
          endTime: P.endTime,
          enabled: P.enabled === 1 ? 0 : 1
        }), X.success(P.enabled === 1 ? "已停用" : "已启用"), g();
      } catch (B) {
        X.error(`操作失败：${B.message}`);
      }
    }
    async function U(P) {
      if (window.confirm("确认删除该委托？"))
        try {
          await l.processSurrogate.remove(P.id), X.success("已删除"), g();
        } catch (B) {
          X.error(`删除失败：${B.message}`);
        }
    }
    return he(g), (P, B) => (o(), u("div", Zu, [
      t("h2", ec, [
        J(Pe, {
          name: "surrogate",
          size: 18
        }),
        B[10] || (B[10] = ee(" 我的委托 ", -1)),
        H(i)(["wf:processSurrogate:save"]) ? (o(), u("button", {
          key: 0,
          class: "jf-btn jf-btn--primary jf-btn--sm",
          onClick: B[0] || (B[0] = (V) => D())
        }, "＋ 新增委托")) : M("", !0)
      ]),
      n.value ? (o(), u("div", tc, "加载中...")) : s.value ? (o(), u("div", nc, w(s.value), 1)) : (o(), u(G, { key: 2 }, [
        c.value.length ? (o(), u("table", lc, [
          B[11] || (B[11] = t("thead", null, [
            t("tr", null, [
              t("th", null, "流程"),
              t("th", null, "被委托人"),
              t("th", null, "生效时间"),
              t("th", null, "状态"),
              t("th", null, "操作")
            ])
          ], -1)),
          t("tbody", null, [
            (o(!0), u(G, null, le(c.value, (V) => (o(), u("tr", {
              key: V.id
            }, [
              t("td", null, w(V.processName || "全部流程"), 1),
              t("td", null, [
                t("strong", null, w(V.surrogate), 1)
              ]),
              t("td", ac, w(H(xe)(V.startTime, !0)) + " ~ " + w(H(xe)(V.endTime, !0)), 1),
              t("td", null, [
                J(Oe, {
                  type: V.enabled === 1 ? "done" : "info"
                }, {
                  default: te(() => [
                    ee(w(V.enabled === 1 ? "启用" : "停用"), 1)
                  ]),
                  _: 2
                }, 1032, ["type"])
              ]),
              t("td", null, [
                t("div", sc, [
                  t("button", {
                    class: "jf-btn jf-btn--ghost jf-btn--sm",
                    onClick: (F) => N(V)
                  }, w(V.enabled === 1 ? "停用" : "启用"), 9, oc),
                  t("button", {
                    class: "jf-btn jf-btn--ghost jf-btn--sm",
                    onClick: (F) => D(V)
                  }, "编辑", 8, ic),
                  t("button", {
                    class: "jf-btn jf-btn--danger jf-btn--sm",
                    onClick: (F) => U(V)
                  }, "删除", 8, rc)
                ])
              ])
            ]))), 128))
          ])
        ])) : (o(), u("div", dc, "暂无委托")),
        r.value > kn ? (o(), u("div", uc, [
          t("button", {
            class: "jf-btn jf-btn--ghost jf-btn--sm",
            disabled: a.value <= 1,
            onClick: B[1] || (B[1] = (V) => C(a.value - 1))
          }, "上一页", 8, cc),
          t("span", fc, w(a.value) + "/" + w(y.value) + "（共 " + w(r.value) + " 条）", 1),
          t("button", {
            class: "jf-btn jf-btn--ghost jf-btn--sm",
            disabled: a.value >= y.value,
            onClick: B[2] || (B[2] = (V) => C(a.value + 1))
          }, "下一页", 8, pc)
        ])) : M("", !0)
      ], 64)),
      J(Ve, {
        visible: v.value,
        "onUpdate:visible": B[9] || (B[9] = (V) => v.value = V),
        title: h.value ? "编辑委托" : "新增委托",
        width: "520px"
      }, {
        default: te(() => [
          t("div", vc, [
            B[12] || (B[12] = t("label", { class: "jf-form-label" }, "流程编码（留空 = 全部流程）", -1)),
            de(t("input", {
              "onUpdate:modelValue": B[3] || (B[3] = (V) => p.value.processName = V),
              class: "jf-input",
              placeholder: "leave"
            }, null, 512), [
              [Te, p.value.processName]
            ])
          ]),
          t("div", mc, [
            B[13] || (B[13] = t("label", { class: "jf-form-label" }, "被委托人 *", -1)),
            J(at, {
              modelValue: j.value,
              "onUpdate:modelValue": B[4] || (B[4] = (V) => j.value = V),
              scene: "surrogate",
              placeholder: "输入姓名/工号搜索"
            }, null, 8, ["modelValue"])
          ]),
          t("div", hc, [
            t("div", yc, [
              B[14] || (B[14] = t("label", { class: "jf-form-label" }, "生效时间 *", -1)),
              de(t("input", {
                "onUpdate:modelValue": B[5] || (B[5] = (V) => p.value.startTime = V),
                class: "jf-input",
                type: "datetime-local"
              }, null, 512), [
                [Te, p.value.startTime]
              ])
            ]),
            t("div", gc, [
              B[15] || (B[15] = t("label", { class: "jf-form-label" }, "失效时间 *", -1)),
              de(t("input", {
                "onUpdate:modelValue": B[6] || (B[6] = (V) => p.value.endTime = V),
                class: "jf-input",
                type: "datetime-local"
              }, null, 512), [
                [Te, p.value.endTime]
              ])
            ])
          ]),
          t("div", bc, [
            B[17] || (B[17] = t("label", { class: "jf-form-label" }, "状态", -1)),
            de(t("select", {
              "onUpdate:modelValue": B[7] || (B[7] = (V) => p.value.enabled = V),
              class: "jf-input"
            }, [...B[16] || (B[16] = [
              t("option", { value: 1 }, "启用", -1),
              t("option", { value: 0 }, "停用", -1)
            ])], 512), [
              [ll, p.value.enabled]
            ])
          ]),
          t("div", kc, [
            t("button", {
              class: "jf-btn jf-btn--ghost",
              onClick: B[8] || (B[8] = (V) => v.value = !1)
            }, "取消"),
            t("button", {
              class: "jf-btn jf-btn--primary",
              disabled: f.value,
              onClick: T
            }, "保存", 8, jc)
          ])
        ]),
        _: 1
      }, 8, ["visible", "title"])
    ]));
  }
});
export {
  Cc as CountersignType,
  pt as FieldPerm,
  zt as JeeflowApiError,
  Jt as JeeflowUiKey,
  xc as JeeflowUiProvider,
  Tc as JfApplyListPage,
  Dn as JfApprovalRecord,
  Nn as JfApproveDrawer,
  Oe as JfBadge,
  Lc as JfCcListPage,
  Ec as JfDonePage,
  Ve as JfDrawer,
  Lt as JfFlowViewer,
  Pe as JfIcon,
  Rt as JfInitiateExtras,
  gt as JfInstanceDetailDrawer,
  Dc as JfLayout,
  Pc as JfMyInstancePage,
  Ac as JfProcessDefinePage,
  Sc as JfProcessDesignPage,
  Ko as JfStartDrawer,
  Oc as JfSurrogatePage,
  qt as JfTabs,
  Mc as JfTodoPage,
  at as JfUserPicker,
  Nc as JfWorkbenchPage,
  _c as PerformType,
  Xe as SchemaForm,
  Ke as SubmitType,
  wc as TaskState,
  Gt as buildPermissionMap,
  _l as createFormRegistry,
  al as createJeeflowApi,
  Cl as createJeeflowUi,
  Vt as extractBizFormData,
  il as findTaskNode,
  _n as firstTaskFormKey,
  Et as firstTaskNode,
  xe as fmtTime,
  cl as initiateExtraFlags,
  Ht as isBuiltinSchemaFormKey,
  dl as isCountersign,
  yt as parseSchema,
  ul as resolveActionBtns,
  sl as resolveAdapters,
  rl as resolveFieldPerm,
  Wt as schemaFieldLabels,
  $n as stateBadgeType,
  Yt as stateLabel,
  an as submitTypeLabel,
  Ic as taskNodes,
  wn as taskStateBadgeType,
  ol as taskStateLabel,
  je as useJeeflowUi
};
