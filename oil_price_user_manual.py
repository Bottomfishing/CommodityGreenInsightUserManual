import webbrowser
import tempfile
import os

html_content = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=yes">
    <title>油价预测系统 | 用户手册</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            background-color: #f5f7fb;
            color: #1e293b;
            line-height: 1.5;
        }

        .container {
            display: flex;
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            box-shadow: 0 0 30px rgba(0,0,0,0.05);
            min-height: 100vh;
        }

        .sidebar {
            width: 280px;
            background: #f8fafc;
            border-right: 1px solid #e2e8f0;
            position: sticky;
            top: 0;
            height: 100vh;
            overflow-y: auto;
            padding: 2rem 1rem;
            flex-shrink: 0;
        }

        .sidebar h3 {
            font-size: 1.1rem;
            font-weight: 600;
            margin-bottom: 1rem;
            padding-left: 0.5rem;
            color: #0f172a;
        }

        .sidebar nav ul {
            list-style: none;
            padding-left: 0;
        }

        .sidebar nav li {
            margin-bottom: 0.4rem;
        }

        .sidebar nav a {
            display: block;
            padding: 0.5rem 0.75rem;
            color: #334155;
            text-decoration: none;
            border-radius: 8px;
            font-size: 0.9rem;
            transition: all 0.2s;
        }

        .sidebar nav a:hover {
            background: #eef2ff;
            color: #1e40af;
        }

        .main-content {
            flex: 1;
            padding: 2rem 2.5rem;
            overflow-x: auto;
            max-width: calc(100% - 280px);
        }

        h1 {
            font-size: 2.2rem;
            margin-bottom: 0.5rem;
            color: #0f172a;
            border-left: 5px solid #3b82f6;
            padding-left: 1rem;
        }

        .sub {
            color: #475569;
            margin-bottom: 2rem;
            border-bottom: 1px solid #e2e8f0;
            padding-bottom: 1rem;
        }

        h2 {
            font-size: 1.6rem;
            margin: 1.8rem 0 1rem 0;
            padding-bottom: 0.4rem;
            border-bottom: 2px solid #e2e8f0;
            color: #0f172a;
        }

        h3 {
            font-size: 1.25rem;
            margin: 1.5rem 0 0.75rem 0;
            color: #1e293b;
        }

        p {
            margin-bottom: 1rem;
            color: #2d3a4e;
        }

        ul, ol {
            margin: 0.75rem 0 1rem 1.5rem;
        }

        li {
            margin-bottom: 0.3rem;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            margin: 1.2rem 0;
            font-size: 0.9rem;
            overflow-x: auto;
            display: block;
        }

        th, td {
            border: 1px solid #cbd5e1;
            padding: 0.6rem 0.8rem;
            text-align: left;
            vertical-align: top;
        }

        th {
            background-color: #f1f5f9;
            font-weight: 600;
        }

        code {
            background: #f1f5f9;
            padding: 0.2rem 0.4rem;
            border-radius: 6px;
            font-family: monospace;
            font-size: 0.85rem;
        }

        .note {
            background: #eef2ff;
            border-left: 4px solid #3b82f6;
            padding: 1rem;
            border-radius: 10px;
            margin: 1.2rem 0;
        }

        .warning {
            background: #fffbeb;
            border-left: 4px solid #f59e0b;
            padding: 1rem;
            border-radius: 10px;
            margin: 1.2rem 0;
        }

        .img-placeholder {
            background: #f1f5f9;
            border-radius: 12px;
            padding: 1rem;
            text-align: center;
            color: #64748b;
            font-size: 0.85rem;
            margin: 1rem 0;
            border: 1px dashed #cbd5e1;
        }

        footer {
            margin-top: 3rem;
            padding-top: 1.5rem;
            border-top: 1px solid #e2e8f0;
            text-align: center;
            font-size: 0.8rem;
            color: #64748b;
        }

        @media (max-width: 800px) {
            .container {
                flex-direction: column;
            }
            .sidebar {
                width: 100%;
                height: auto;
                position: relative;
                border-right: none;
                border-bottom: 1px solid #e2e8f0;
                padding: 1rem;
            }
            .main-content {
                max-width: 100%;
                padding: 1.5rem;
            }
        }
    </style>
</head>
<body>
<div class="container">
    <aside class="sidebar">
        <h3>📘 目录</h3>
        <nav>
            <ul>
                <li><a href="#overview">1. 概论</a></li>
                <li><a href="#environment">2. 运行环境</a></li>
                <li><a href="#system-intro">3. 系统介绍</a></li>
                <li><a href="#user-guide">4. 普通用户操作指南</a></li>
                <li><a href="#results">5. 生成结果含义</a></li>
                <li><a href="#code-explanation">6. 代码讲解</a></li>
                <li><a href="#faq">7. 常见问题与注意事项</a></li>
            </ul>
        </nav>
    </aside>
    <main class="main-content">
        <h1>油价预测系统用户手册</h1>
        <div class="sub">适用于 Streamlit Web 前端 + 多变量 GRU 预测主程序</div>

        <section id="overview">
            <h2>1. 概论</h2>
            <p>本系统是一个面向原油价格预测和绿色股票价格预测场景构建的可视化分析平台，整体由两个部分组成：一是基于 Streamlit 搭建的 Web 前端，负责数据上传、参数设置、任务启动、训练监控、结果预览与文件导出；二是后端预测主程序，负责数据加载、特征工程、特征筛选、序列构建、GRU 模型训练、结果评估与输出文件生成。系统的设计目标并不是只给出一个"最终数字"，而是让用户能够看到从数据输入到结果输出的完整过程，兼顾易用性、可解释性和工程化管理。</p>
            <p>从前端角度看，普通用户无需直接修改 Python 代码，只需要准备符合规范的数据压缩包，设置 Top-N、训练轮数等少量参数，即可通过按钮触发整套流程。系统会在后台启动训练进程，并在页面中实时展示程序运行时产生的日志文件（run.log）、training_log.csv 对应的训练曲线以及最终预测结果。对于不懂代码的使用者，这种"上传数据—点击运行—查看结果"的交互模式，显著降低了使用门槛。</p>
            <p>从建模角度看，系统整合了 WTI 原油期货/现货、金融市场变量、供给侧数据、情绪指标以及地缘事件等多源数据，并通过严格因果性的特征工程方法，尽量确保每个时点的特征只来自该时点及其之前的信息，避免未来信息泄露。随后，系统使用随机森林进行 Top-N 特征筛选，并以 GRU 神经网络作为核心预测模型，对未来油价进行建模和评估。</p>
            <p>当前系统已预留多项扩展功能以增强整体智能化水平，包括两个基于大模型的 AI 辅助页面（新手引导 AI 与结果分析 AI），分别用于帮助用户快速上手系统及对预测结果进行智能解读。同时，系统还预留了新能源整合预测模块，用于支持多能源数据的扩展分析，该模块需用户提供符合要求的数据压缩包（zip）作为输入方可运行。</p>
        </section>

        <section id="environment">
            <h2>2. 运行环境</h2>
            <h3>2.1 硬件与操作系统建议</h3>
            <ul>
                <li>操作系统：Windows 10/11、Linux 或 macOS 均可，Windows 环境更常见。</li>
                <li>处理器：建议多核 CPU。代码默认关闭 GPU，因此主要按 CPU 方式运行。</li>
                <li>内存：建议 8GB 以上，若数据量较大建议 16GB。</li>
                <li>磁盘：建议预留 2GB 以上空间，用于解压目录、日志、模型和结果文件。</li>
            </ul>
            <h3>2.2 Python 版本建议</h3>
            <p>建议使用 Python 3.10 或 3.11，以更好兼容 Streamlit、TensorFlow、scikit-learn 等库。</p>
            <h3>2.3 主要依赖库</h3>
            <ul>
                <li>streamlit：构建 Web 前端页面。</li>
                <li>pandas、numpy：完成数据读取、清洗、特征处理与表格输出。</li>
                <li>matplotlib：生成预测图、收益图、方向图。</li>
                <li>scikit-learn：用于随机森林特征选择、评估指标计算、归一化等。</li>
                <li>tensorflow / keras：用于搭建并训练 GRU 模型。</li>
                <li>scipy：用于异常值处理、统计特征计算。</li>
                <li>lightgbm：可选依赖，未安装时会自动回退。</li>
            </ul>
            <h3>2.4 数据目录要求</h3>
            <table>
                <thead><tr><th>目录/文件</th><th>是否必须</th><th>作用说明</th></tr></thead>
                <tbody>
                    <tr><td>raw_data/</td><td>是</td><td>存放 WTI 期货、现货、DXY、SP500、VIX、OVX、US10Y 等基础数据</td></tr>
                    <tr><td>能源基本面与下游产业/</td><td>是</td><td>存放库存、产量、钻井机数量、地缘事件等基本面数据</td></tr>
                    <tr><td>raw_data/WTI_futuresprice.csv</td><td>是</td><td>系统启动校验的关键文件，缺失则不能运行</td></tr>
                    <tr><td>情绪指标相关 CSV</td><td>否</td><td>用于补充 oil price、gas price 等搜索趋势数据</td></tr>
                </tbody>
            </table>
            <h3>2.5 输出目录说明</h3>
            <p>每次运行后，系统会在 web_runs 下创建类似 run_年月日_时分秒_topN 的目录，专门保存本轮日志、模型、表格和图片。</p>
        </section>

        <section id="system-intro">
            <h2>3. 系统介绍</h2>
            <p>本系统可以理解为"前端控制台 + 后端预测引擎"的组合系统。</p>
            <h3>3.1 总体架构</h3>
            <p>流程为：上传数据 → 参数设置 → 后台训练 → 训练监控 → 结果预览 → 下载导出。</p>
            <div class="img-placeholder">📊 架构流程图（示意）</div>
            <h3>3.2 前端模块</h3>
            <ul>
                <li>"运行"页：上传 zip、设置 Top-N、Epochs、EarlyStopping 以及未来 H 天预测选项。</li>
                <li>"训练监控"页：查看 training_log.csv、prediction_results.csv 和 run.log 状态，并自动刷新训练曲线。</li>
                <li>"结果预览"页：查看表格、图片、风险分类、回测结果、未来预测和 run.log。</li>
                <li>"下载/导出"页：集中导出当前运行目录中的输出文件。</li>
            </ul>
            <h3>3.3 后端核心模块</h3>
            <table>
                <thead><tr><th>模块名称</th><th>主要职责</th><th>说明</th></tr></thead>
                <tbody>
                    <tr><td>OilPriceDataLoader</td><td>加载原始数据</td><td>读取期货/现货、金融变量、库存、产量、钻井机、情绪指标和地缘事件等数据</td></tr>
                    <tr><td>FeatureEngineer</td><td>构造特征</td><td>生成价格、金融、基本面、技术指标、波动率、市场结构、季节性、情绪等特征</td></tr>
                    <tr><td>DataPreprocessor</td><td>数据预处理</td><td>执行缺失值处理、异常值处理、时间切分和随机森林 Top-N 特征选择</td></tr>
                    <tr><td>OilPricePredictor</td><td>建模预测</td><td>构建 GRU 网络、训练模型、还原价格、评估性能并输出结果文件</td></tr>
                </tbody>
            </table>
            <h3>3.4 系统特点</h3>
            <ul>
                <li>采用多源数据融合，而不是只看历史油价。</li>
                <li>强调严格因果性，尽量避免未来信息泄露。</li>
                <li>通过随机森林 Top-N 特征选择提升可控性和可解释性。</li>
                <li>通过 GRU 建模捕捉时间序列依赖关系。</li>
                <li>支持后台训练、实时监控与结果导出，前端交互性完整。</li>
            </ul>
        </section>

        <section id="user-guide">
            <h2>4. 普通用户操作指南</h2>
            <h3>4.1 启动系统</h3>
            <p>安装依赖后进入项目目录，执行 Streamlit 启动命令：<code>streamlit run streamlit_app_0325.py</code>，浏览器会打开 Web 页面。左侧栏会显示要求、平台简介和历史运行目录。</p>
            <h3>4.2 准备数据压缩包</h3>
            <p>准备一个 zip 数据包，里面至少包含 raw_data 和“能源基本面与下游产业”两个文件夹。若目录或关键文件缺失，系统会报错并显示目录结构片段。</p>
            <div class="img-placeholder">📁 压缩包结构示意</div>
            <h3>4.3 进入“运行”页设置参数</h3>
            <ul>
                <li>随机森林特征选择 Top-N：决定保留多少个最重要特征。</li>
                <li>训练轮数 Epochs：决定最大训练轮次。</li>
                <li>启用 EarlyStopping：建议勾选，以减少无效训练并防止过拟合。</li>
                <li>实盘预测（可选）：可设置截止日期和未来 H 天数，用于生成 future_forecast.csv。</li>
            </ul>
            <div class="img-placeholder">⚙️ 参数设置界面示意</div>
            <h3>4.4 点击“开始运行”</h3>
            <p>点击后系统先解压并校验数据，再在 web_runs 中创建输出目录，并以后台进程方式启动训练任务。</p>
            <h3>4.5 查看训练监控</h3>
            <p>在“训练监控”页中，可以监控当前任务、最近更新目录、左侧选择目录或手动输入目录。若 training_log.csv 尚未生成，可先看 run.log 最后几行，判断程序是在数据处理阶段还是训练阶段。</p>
            <h3>4.6 结果预览 + 自主选择是否进行新能源预测</h3>
            <ul>
                <li>查看每日预测和完整结果表。</li>
                <li>查看预测价格图、收益图和方向图。</li>
                <li>查看风险分类、回测结果、未来 H 天预测和 Markdown 报告。</li>
                <li>必要时查看 run.log 末尾内容辅助定位问题。</li>
                <li>选择是否进行新能源股票预测。</li>
            </ul>
            <div class="img-placeholder">📈 结果预览界面示意</div>
            <h3>4.7 下载导出</h3>
            <p>在“下载/导出”页中导出本次运行目录中的文件，建议至少保留 prediction_results.csv、training_log.csv、gru_model.h5 和主要图片文件。</p>
            <div class="warning">
                <strong>⚠️ 普通用户最常见的错误：</strong><br>
                - 上传的不是 zip，而是文件夹或单个 csv。<br>
                - 压缩包里缺少 raw_data 或“能源基本面与下游产业”。<br>
                - raw_data 中缺少 WTI_futuresprice.csv。<br>
                - Top-N 设得过小导致模型欠拟合。<br>
                - 训练刚开始就急着找 prediction_results.csv，此时文件可能尚未生成。
            </div>
        </section>

        <section id="results">
            <h2>5. 生成结果含义</h2>
            <h3>5.1 核心输出文件</h3>
            <table>
                <thead><tr><th>文件名</th><th>类型</th><th>含义说明</th></tr></thead>
                <tbody>
                    <tr><td>prediction_results.csv</td><td>结果表</td><td>保存真实价格、预测价格、真实收益和预测收益，是最重要的分析文件</td></tr>
                    <tr><td>training_log.csv</td><td>日志表</td><td>记录每轮 epoch 的 loss、val_loss、mae 等信息，用于判断是否收敛</td></tr>
                    <tr><td>gru_predictions.png</td><td>图片</td><td>展示真实价格与预测价格的对比曲线</td></tr>
                    <tr><td>gru_returns.png</td><td>图片</td><td>展示真实收益率与预测收益率的对比曲线</td></tr>
                    <tr><td>direction_prediction.png</td><td>图片</td><td>展示真实方向与预测方向，用于观察趋势判断能力</td></tr>
                    <tr><td>gru_model.h5</td><td>模型文件</td><td>保存训练完成后的 GRU 模型参数，可用于加载和复现</td></tr>
                </tbody>
            </table>
            <div class="img-placeholder">📊 prediction_results.csv 预览示意</div>
            <div class="img-placeholder">📈 gru_predictions.png 示意（油价预测）</div>
            <div class="img-placeholder">📉 gru_returns.png 示意（收益预测）</div>
            <h3>5.2 扩展输出文件</h3>
            <ul>
                <li><code>all_features_data.csv</code>：特征筛选后并附带数据集分段标记的整体特征数据。</li>
                <li><code>model_input_data.csv</code>：真正送入模型的特征、目标列和 train/val/test 标记。</li>
                <li><code>risk_signal_classification.csv</code>：风险等级和交易信号分类。</li>
                <li><code>backtest_results.csv</code> / <code>backtest_metrics.csv</code>：回测明细与指标。</li>
                <li><code>future_forecast.csv</code>：未来 H 天递推预测结果。</li>
                <li><code>run.log</code>：运行全过程日志，报错时最先检查。</li>
            </ul>
            <div class="img-placeholder">📊 回测结果图示意（策略净值 vs 买入持有）</div>
            <h3>5.3 prediction_results.csv 字段解释</h3>
            <p>Date_base（预测基准日）、Date_target（预测目标日）、BasePrice_P_t、Actual_P_t_plus_H、GRU_Pred_P_t_plus_H、Actual_Return、GRU_Pred_Return。</p>
            <h3>5.4 training_log.csv 判断</h3>
            <p>loss 和 val_loss 逐步下降并稳定表示正常；若 loss 很低而 val_loss 很高，表示过拟合；二者很高表示欠拟合。</p>
            <h3>5.5 图片结果含义</h3>
            <p><code>gru_predictions.png</code> 价格拟合形态；<code>gru_returns.png</code> 收益波动同步性；<code>direction_prediction.png</code> 涨跌方向判断能力。</p>
            <h3>5.6 风险分类、回测与未来预测</h3>
            <p><code>risk_signal_classification.csv</code> 用于说明风险等级和 LONG/SHORT/FLAT 等策略信号；<code>backtest_results.csv</code> 与 <code>backtest_metrics.csv</code> 用于评估策略表现；<code>future_forecast.csv</code> 则表示模型对未来若干天的前瞻预测。</p>
        </section>

        <section id="code-explanation">
            <h2>6. 代码讲解</h2>
            <h3>6.1 前端脚本的作用</h3>
            <ul>
                <li>负责页面布局、美化和侧边栏说明。</li>
                <li>负责接收用户上传的 zip 数据包。</li>
                <li>负责解压、识别根目录和校验关键文件。</li>
                <li>负责把参数传给后台主程序，并通过 subprocess 启动训练进程。</li>
                <li>负责监控 run.log 与 training_log.csv，并展示结果文件和图片。</li>
            </ul>
            <h3>6.2 前端辅助函数</h3>
            <ul>
                <li><code>extract_zip_to_dir</code>：解压 zip，并尽量修复中文目录乱码问题。</li>
                <li><code>find_data_root</code>：容许压缩包外面再套一层目录，提高容错率。</li>
                <li><code>validate_data_root</code>：检查关键目录和 WTI_futuresprice.csv 是否齐全。</li>
                <li><code>start_background_run</code>：后台启动训练任务，并同步写入 run.log。</li>
                <li><code>render_training_dashboard</code>：把 training_log.csv 与 prediction_results.csv 可视化。</li>
                <li><code>tail_text_file</code>：只读取日志末尾若干行，避免页面过长。</li>
            </ul>
            <h3>6.3 数据加载模块</h3>
            <ul>
                <li><code>load_wti_data</code>：读取 WTI 期货和现货价格，计算基差 Basis。</li>
                <li><code>load_financial_data</code>：读取 DXY、SP500、US10Y、VIX、OVX 等金融变量。</li>
                <li><code>load_supply_data</code>：读取库存、产量和活跃钻井机数量等供给侧数据。</li>
                <li><code>load_sentiment_data</code>：读取 oil price、gas price 等搜索趋势数据。</li>
                <li><code>load_geopolitical_events</code>：把地缘事件转化为可建模变量。</li>
                <li><code>load_all_data</code>：按日期合并并整理为统一总表。</li>
            </ul>
            <h3>6.4 特征工程模块</h3>
            <ul>
                <li>价格自身特征：收益率、方向、滞后值、动量、分位数等。</li>
                <li>金融市场特征：DXY、VIX、OVX、SP500、US10Y 等变化率和动量。</li>
                <li>基本面特征：库存、产量、钻井平台和供需平衡。</li>
                <li>技术指标：移动平均线、RSI、MACD、布林带、ATR。</li>
                <li>波动率特征：历史波动率、年化波动率、偏度、峰度等。</li>
                <li>市场结构特征：基差、期限结构、跨市场价差。</li>
                <li>季节性特征：月份、季度、节假日、旺淡季。</li>
                <li>情绪特征与地缘特征：搜索趋势、事件影响程度等。</li>
            </ul>
            <p><strong>注：</strong> 这里特别值得强调的是 <code>shift(1)</code>。它表示模型只使用过去信息，不偷看未来，这体现了时间序列分析中的严格因果性原则。</p>
            <h3>6.5 预处理与特征筛选模块</h3>
            <ul>
                <li>对价格类、供给类、情绪类和宏观慢变量做前向填充。</li>
                <li>支持 Z-score 删除异常值和 Winsorize 截断异常值。</li>
                <li>按日期切分 Train、Val、Test。</li>
                <li>仅用训练集做随机森林 Top-N 特征选择。</li>
            </ul>
            <h3>6.6 GRU 部分</h3>
            <p>GRU 属于循环神经网络，适合处理时间序列。当前主流程采用多层堆叠 GRU，units 为 [256,128,64]，并结合 Dropout、Adam、Huber、ReduceLROnPlateau、CSVLogger 和 EarlyStopping。</p>
            <h3>6.7 模型训练与评估流程</h3>
            <ul>
                <li>加载数据并执行特征工程。</li>
                <li>创建未来价格目标列 WTI_Price_t_plus_H。</li>
                <li>处理缺失值并按日期切分数据。</li>
                <li>在训练集上做随机森林 Top-N 特征选择。</li>
                <li>保存 all_features_data.csv 与 model_input_data.csv。</li>
                <li>在 Train+Val 上做时间序列交叉验证。</li>
                <li>构造时间窗口序列并训练 GRU。</li>
                <li>在测试集上计算 MAE、RMSE、MAPE、R2 和方向准确率。</li>
                <li>输出图片、结果表和模型文件。</li>
            </ul>
            <h3>6.8 指标含义</h3>
            <ul>
                <li>MAE：平均绝对误差，越小越好。</li>
                <li>RMSE：均方根误差，对大误差更敏感。</li>
                <li>MAPE：平均绝对百分比误差。</li>
                <li>R2：决定系数，越接近 1 越好。</li>
                <li>Direction Accuracy：方向预测准确率。</li>
            </ul>
            <div class="note">
                <strong>💡 代码亮点：</strong><br>
                - 多源数据融合而非单一价格序列。<br>
                - 强调因果性，尽量避免数据泄露。<br>
                - 采用随机森林特征选择 + GRU 的组合。<br>
                - 具有交叉验证、训练日志、可视化和模型保存等完整闭环。<br>
                - 前端具备一定产品化设计，便于普通用户使用。
            </div>
        </section>

        <section id="faq">
            <h2>7. 常见问题与注意事项</h2>
            <ul>
                <li>若提示缺少目录或文件，先检查压缩包层级与命名。</li>
                <li>若任务很快结束，优先查看 run.log 最后几行。</li>
                <li>若结果较差，可尝试适当增大 Top-N 或 Epochs，但不要盲目无限增大。</li>
                <li>若训练较慢，先确认是否启用 EarlyStopping。</li>
                <li>训练过程中不要刷新“运行”页面，避免重复启动任务；监控页面会自动更新。</li>
            </ul>
        </section>

        <footer>
            © 油价预测系统 | 基于 Streamlit + GRU 多变量时序预测 | 本手册适用于前端+后端完整版本
        </footer>
    </main>
</div>
</body>
</html>
"""

def main():
    # 创建临时 HTML 文件
    fd, path = tempfile.mkstemp(suffix='.html', prefix='oil_price_manual_', text=True)
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        f.write(html_content)
    # 在默认浏览器中打开
    webbrowser.open('file://' + path)
    print(f"用户手册已生成并打开: {path}")

if __name__ == "__main__":
    main()