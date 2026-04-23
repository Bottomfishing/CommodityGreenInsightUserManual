import { ref, type Ref } from "vue";

export function useMonitorDashboard(
  activePage: Ref<string>,
  dashboardData: Ref<any>,
) {
  const lossChartRef = ref<HTMLDivElement | null>(null);
  const priceChartRef = ref<HTMLDivElement | null>(null);
  const returnChartRef = ref<HTMLDivElement | null>(null);
  const echartsReady = ref(false);

  let lossChart: any = null;
  let priceChart: any = null;
  let returnChart: any = null;

  function getEcharts() {
    return (window as any).echarts || null;
  }

  async function ensureEchartsReady() {
    if (echartsReady.value && getEcharts()) return;
    if (getEcharts()) {
      echartsReady.value = true;
      return;
    }
    await new Promise<void>((resolve, reject) => {
      const script = document.createElement("script");
      script.src = "https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js";
      script.onload = () => resolve();
      script.onerror = () => reject(new Error("ECharts 加载失败"));
      document.head.appendChild(script);
    });
    echartsReady.value = true;
  }

  function renderMonitorCharts() {
    const ec = getEcharts();
    if (!ec || activePage.value !== "monitor") return;

    const lossSeries = Array.isArray(dashboardData.value?.loss_series) ? dashboardData.value.loss_series : [];
    const priceSeries = Array.isArray(dashboardData.value?.price_series) ? dashboardData.value.price_series : [];
    const returnSeries = Array.isArray(dashboardData.value?.return_series) ? dashboardData.value.return_series : [];

    if (lossChartRef.value && lossSeries.length) {
      if (!lossChart) lossChart = ec.init(lossChartRef.value);
      const epochs = lossSeries.map((r: any) => r.epoch);
      const losses = lossSeries.map((r: any) => r.loss ?? r.train_loss);
      const valLosses = lossSeries.map((r: any) => r.val_loss);
      const chartSeries: any[] = [
        { name: "train_loss", type: "line", data: losses, smooth: true, symbol: "none", lineStyle: { color: "#38bdf8", width: 2 } },
      ];
      if (valLosses.some((v: any) => v !== null && v !== undefined)) {
        chartSeries.push({
          name: "val_loss",
          type: "line",
          data: valLosses,
          smooth: true,
          symbol: "none",
          lineStyle: { color: "#22c55e", width: 2 },
        });
      }
      lossChart.setOption({
        backgroundColor: "transparent",
        tooltip: { trigger: "axis" },
        legend: { data: chartSeries.map((s) => s.name), bottom: 0, textStyle: { color: "#94a3b8" } },
        xAxis: { type: "category", data: epochs, name: "Epoch", axisLabel: { color: "#94a3b8" } },
        yAxis: { type: "value", name: "Loss", axisLabel: { color: "#94a3b8" } },
        grid: { left: 45, right: 18, top: 16, bottom: 34 },
        series: chartSeries,
      });
    }

    if (priceChartRef.value && priceSeries.length) {
      if (!priceChart) priceChart = ec.init(priceChartRef.value);
      const dates = priceSeries.map((r: any) => r.Date_target || r.date);
      const actual = priceSeries.map((r: any) => r.Actual_P_t_plus_H ?? r.actual);
      const pred = priceSeries.map((r: any) => r.GRU_Pred_P_t_plus_H ?? r.pred);
      priceChart.setOption({
        backgroundColor: "transparent",
        tooltip: { trigger: "axis" },
        legend: { data: ["Actual_Price", "GRU_Pred_Price"], bottom: 0, textStyle: { color: "#94a3b8" } },
        xAxis: { type: "category", data: dates, axisLabel: { color: "#94a3b8", rotate: 25, fontSize: 10 } },
        yAxis: { type: "value", name: "Price", axisLabel: { color: "#94a3b8" } },
        grid: { left: 55, right: 18, top: 16, bottom: 42 },
        series: [
          { name: "Actual_Price", type: "line", data: actual, smooth: true, symbol: "none", lineStyle: { color: "#22d3ee", width: 2 } },
          { name: "GRU_Pred_Price", type: "line", data: pred, smooth: true, symbol: "none", lineStyle: { color: "#f59e0b", width: 2 } },
        ],
      });
    }

    if (returnChartRef.value && returnSeries.length) {
      if (!returnChart) returnChart = ec.init(returnChartRef.value);
      const dates = returnSeries.map((r: any) => r.Date_target || r.date);
      const actual = returnSeries.map((r: any) => r.Actual_Return);
      const pred = returnSeries.map((r: any) => r.GRU_Pred_Return);
      returnChart.setOption({
        backgroundColor: "transparent",
        tooltip: { trigger: "axis" },
        legend: { data: ["Actual_Return", "GRU_Pred_Return"], bottom: 0, textStyle: { color: "#94a3b8" } },
        xAxis: { type: "category", data: dates, axisLabel: { color: "#94a3b8", rotate: 25, fontSize: 10 } },
        yAxis: { type: "value", name: "Return", axisLabel: { color: "#94a3b8" } },
        grid: { left: 55, right: 18, top: 16, bottom: 42 },
        series: [
          { name: "Actual_Return", type: "line", data: actual, smooth: true, symbol: "none", lineStyle: { color: "#38bdf8", width: 2 } },
          { name: "GRU_Pred_Return", type: "line", data: pred, smooth: true, symbol: "none", lineStyle: { color: "#22c55e", width: 2 } },
        ],
      });
    }
  }

  function resizeCharts() {
    lossChart?.resize();
    priceChart?.resize();
    returnChart?.resize();
  }

  function disposeMonitorCharts() {
    lossChart?.dispose();
    priceChart?.dispose();
    returnChart?.dispose();
    lossChart = null;
    priceChart = null;
    returnChart = null;
  }

  return {
    lossChartRef,
    priceChartRef,
    returnChartRef,
    ensureEchartsReady,
    renderMonitorCharts,
    resizeCharts,
    disposeMonitorCharts,
  };
}
