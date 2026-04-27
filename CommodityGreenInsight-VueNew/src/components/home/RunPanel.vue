<template>
  <div class="work-panel">
    <div class="module-head">
      <span class="module-head-tag">RUN CONFIG</span>
      <span class="module-head-title">运行配置面板</span>
    </div>
    <dv-decoration-3 class="module-head-line" />

    <div class="form-grid">
      <label class="field">
        <span>模型命名</span>
        <input v-model.trim="runForm.modelName" type="text" placeholder="例如：我的模型A" maxlength="40" />
      </label>
      <label class="field">
        <span class="field-label"
          >数据 ZIP（可不上传，默认使用我们的数据集）
          <span class="help-tip">
            ?
            <span class="help-popover">
              <strong>ZIP 格式说明</strong>
              <div class="help-group">
                <span class="help-group-title">必需</span>
                <ul>
                  <li>可不上传 ZIP，不上传时默认使用系统内置 `OilData`</li>
                  <li>上传时仅支持 `.zip` 压缩包</li>
                  <li>包含 `raw_data/` 与 `能源基本面与下游产业/`</li>
                  <li>`raw_data/WTI_futuresprice.csv`（需 `Date`、`ClosePrice` 列）</li>
                </ul>
              </div>
              <div class="help-group">
                <span class="help-group-title">可选增强</span>
                <ul>
                  <li>`raw_data/WTI_spotprice.xls`、`DXY_Index.csv`、`SP500_Index.csv`</li>
                  <li>`US10Y_Yield.csv`、`VIX_index.csv`、`OVX_index.csv`</li>
                  <li>`情绪指标/oil price.csv`、`情绪指标/gas price.csv`</li>
                  <li>`一、原油供需情况/美国商业原油库存.csv`</li>
                  <li>`一、原油供需情况/美国原油产量周度数据.csv`</li>
                  <li>`一、原油供需情况/活跃钻井机数量.xlsx`、`三、地缘大事记.xlsx`</li>
                </ul>
              </div>
            </span>
          </span>
        </span>
        <input type="file" accept=".zip" @change="emit('file-selected', $event)" />
      </label>
      <label class="field">
        <span class="field-label"
          >TopN
          <span class="help-tip" data-tip="特征筛选数量，越大保留信息越多，但训练可能更慢。推荐 30~80。">?</span>
        </span>
        <input v-model.number="runForm.topN" type="number" min="5" max="200" />
      </label>
      <label class="field">
        <span class="field-label"
          >Epochs
          <span class="help-tip" data-tip="训练轮数。轮数越高拟合越充分，但过高可能过拟合。">?</span>
        </span>
        <input v-model.number="runForm.epochs" type="number" min="1" max="2000" />
      </label>
      <label class="field">
        <span class="field-label"
          >预测步长
          <span class="help-tip" data-tip="向后预测的时间步数量。数值越大，长期预测不确定性越高。">?</span>
        </span>
        <input v-model.number="runForm.forecastSteps" type="number" min="0" max="90" />
      </label>
      <label class="field">
        <span class="field-label"
          >截止日期（可选）
          <span class="help-tip" data-tip="仅使用该日期及之前的数据训练，用于回测或固定时间窗口实验。">?</span>
        </span>
        <input v-model="runForm.cutoffDate" type="date" />
      </label>
      <label class="checkbox-field">
        <input v-model="runForm.enableEarlyStopping" type="checkbox" />
        <span>启用早停</span>
      </label>
    </div>

    <div class="feature-actions">
      <button class="feature-btn feature-btn--primary" :disabled="runLoading" @click="emit('submit')">
        {{ runLoading ? "启动中..." : "开始运行" }}
      </button>
      <button class="feature-btn" :disabled="!selectedRunId || runLoading" @click="emit('stop')">
        停止当前运行
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{
  runForm: {
    modelName: string;
    topN: number;
    epochs: number;
    forecastSteps: number;
    cutoffDate: string;
    enableEarlyStopping: boolean;
  };
  runLoading: boolean;
  selectedRunId: string;
}>();

void props;

const emit = defineEmits<{
  (e: "file-selected", event: Event): void;
  (e: "submit"): void;
  (e: "stop"): void;
}>();
</script>

<style scoped>
.work-panel {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 10px;
  border-radius: 12px;
  border: 1px solid rgba(56, 189, 248, 0.16);
  background:
    linear-gradient(180deg, rgba(8, 18, 38, 0.68), rgba(3, 9, 24, 0.72)),
    radial-gradient(circle at 90% 10%, rgba(56, 189, 248, 0.09), transparent 45%);
  box-shadow:
    inset 0 0 24px rgba(56, 189, 248, 0.05),
    0 10px 24px rgba(2, 6, 23, 0.24);
}
.module-head {
  display: flex;
  align-items: baseline;
  gap: 10px;
}
.module-head-tag {
  display: inline-flex;
  align-items: center;
  padding: 3px 8px;
  border-radius: 999px;
  font-size: 10px;
  letter-spacing: 0.12em;
  color: #67e8f9;
  background: rgba(8, 145, 178, 0.18);
  border: 1px solid rgba(34, 211, 238, 0.32);
}
.module-head-title {
  font-size: 15px;
  font-weight: 700;
  color: #e2e8f0;
}
.module-head-line {
  width: 220px;
  height: 18px;
}
.form-grid {
  width: 100%;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}
.field,
.checkbox-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
  color: rgba(191, 219, 254, 0.92);
  font-size: 12px;
}
.field-label {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.help-tip {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  border: 1px solid rgba(56, 189, 248, 0.6);
  background: rgba(8, 47, 73, 0.75);
  color: #a5f3fc;
  font-size: 11px;
  line-height: 14px;
  text-align: center;
  cursor: help;
  user-select: none;
}
/* 通用短提示：给带 data-tip 的问号使用 */
.help-tip[data-tip]::after {
  content: attr(data-tip);
  position: absolute;
  left: 50%;
  bottom: calc(100% + 8px);
  transform: translateX(-50%);
  width: 240px;
  max-width: min(70vw, 300px);
  padding: 7px 9px;
  border-radius: 8px;
  border: 1px solid rgba(56, 189, 248, 0.35);
  background: rgba(2, 8, 23, 0.96);
  color: #dbeafe;
  font-size: 11px;
  line-height: 1.45;
  text-align: left;
  white-space: normal;
  box-shadow: 0 10px 26px rgba(2, 6, 23, 0.45);
  opacity: 0;
  visibility: hidden;
  pointer-events: none;
  transition: opacity 0.16s ease;
  z-index: 10;
}
.help-popover {
  position: absolute;
  left: 50%;
  bottom: calc(100% + 8px);
  transform: translateX(-50%);
  width: 360px;
  max-width: min(78vw, 420px);
  padding: 10px 12px;
  border-radius: 8px;
  border: 1px solid rgba(56, 189, 248, 0.35);
  background: rgba(2, 8, 23, 0.96);
  color: #dbeafe;
  font-size: 11px;
  line-height: 1.45;
  box-shadow: 0 10px 26px rgba(2, 6, 23, 0.45);
  text-align: left;
  white-space: normal;
  opacity: 0;
  visibility: hidden;
  pointer-events: none;
  transition: opacity 0.16s ease;
  z-index: 10;
}
.help-popover strong {
  display: block;
  margin-bottom: 6px;
  color: #cffafe;
  font-size: 12px;
}
.help-group + .help-group {
  margin-top: 6px;
}
.help-group-title {
  display: inline-block;
  margin-bottom: 2px;
  color: #7dd3fc;
}
.help-group ul {
  margin: 0;
  padding-left: 16px;
}
.help-group li {
  margin: 1px 0;
}
.help-tip[data-tip]:hover::after {
  opacity: 1;
  visibility: visible;
}
.help-tip:hover .help-popover {
  opacity: 1;
  visibility: visible;
}
.checkbox-field {
  flex-direction: row;
  align-items: center;
  margin-top: 20px;
}
.field input {
  border: 1px solid rgba(56, 189, 248, 0.25);
  border-radius: 8px;
  background: rgba(4, 16, 38, 0.72);
  color: #e0f2fe;
  padding: 8px 10px;
  transition: all 0.2s;
}
.field input:focus {
  outline: none;
  border-color: rgba(34, 211, 238, 0.7);
  box-shadow: 0 0 0 3px rgba(34, 211, 238, 0.12);
}
.field input[type="file"] {
  padding: 6px 8px;
  cursor: pointer;
}
.field input[type="file"]::file-selector-button {
  margin-right: 10px;
  border: 1px solid rgba(34, 211, 238, 0.55);
  border-radius: 7px;
  padding: 6px 12px;
  font-size: 12px;
  color: #ecfeff;
  background: linear-gradient(135deg, rgba(14, 116, 144, 0.72), rgba(37, 99, 235, 0.62));
  box-shadow: 0 4px 10px rgba(14, 116, 144, 0.28);
  cursor: pointer;
  transition: all 0.2s ease;
}
.field input[type="file"]::file-selector-button:hover {
  border-color: rgba(34, 211, 238, 0.75);
  transform: translateY(-1px);
}
.field input[type="file"]::-webkit-file-upload-button {
  margin-right: 10px;
  border: 1px solid rgba(34, 211, 238, 0.55);
  border-radius: 7px;
  padding: 6px 12px;
  font-size: 12px;
  color: #ecfeff;
  background: linear-gradient(135deg, rgba(14, 116, 144, 0.72), rgba(37, 99, 235, 0.62));
  box-shadow: 0 4px 10px rgba(14, 116, 144, 0.28);
  cursor: pointer;
  transition: all 0.2s ease;
}
.field input[type="file"]::-webkit-file-upload-button:hover {
  border-color: rgba(34, 211, 238, 0.75);
  transform: translateY(-1px);
}
.feature-actions {
  display: flex;
  gap: 10px;
  margin-top: 6px;
}
.feature-btn {
  border: 1px solid rgba(56, 189, 248, 0.28);
  background: rgba(7, 25, 52, 0.68);
  color: #bae6fd;
  border-radius: 8px;
  padding: 8px 14px;
  cursor: pointer;
  transition: all 0.2s;
}
.feature-btn:hover {
  border-color: rgba(34, 211, 238, 0.55);
  color: #e0f2fe;
  transform: translateY(-1px);
}
.feature-btn--primary {
  border-color: rgba(34, 211, 238, 0.55);
  background: linear-gradient(135deg, rgba(14, 116, 144, 0.62), rgba(37, 99, 235, 0.55));
  color: #ecfeff;
  box-shadow: 0 4px 16px rgba(14, 116, 144, 0.3);
}
.feature-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
