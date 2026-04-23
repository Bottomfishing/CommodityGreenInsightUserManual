# 大宗绿测_基于油价因子的绿色金融产品预测与风险分析源代码
大宗绿测_基于油价因子的绿色金融产品预测与风险分析git源代码

[oil_price_prediction_main_0309.py](oil_price_prediction_main_0309.py)  -为深度学习主程序，油价预测程序，采用随机森林进行特征选择（选择topo15为最佳方案），同时进行了细致的特征工程，后采用gru为模型预测，用前20天的数据预测后一天的数据

[predict_new_energy_from_gru.py](predict_new_energy_from_gru.py)    -为绿色股票预测部分，采用油价输出的结果csv和绿色股票自身时间序列csv作为特征，结合推导多篇论文的动力学公式，其中构造了油价意外利率、油价意外波动率，油价预期利率、油价预期波动率、略色股票滞后等多个特征进行预测

[predict_bond_from_gru.py](predict_bond_from_gru.py)    -为绿色债券预测，也是以石油输出的csv为输入，和绿色股票预测部分相似

[streamlit_app_0325.py](streamlit_app_0325.py)  -web，由streamlit前后端一体搭建

[ai_expert_panel.py](ai_expert_panel.py)    -植入的ai api,api key直接写在里边了

[web_runs](web_runs)    -web中的历史记录，每次web训练的结果都在里边

[OilData](OilData)  -油价相关dataset

[绿色股票指数](%E7%BB%BF%E8%89%B2%E8%82%A1%E7%A5%A8%E6%8C%87%E6%95%B0)    -绿色股票相关dataset

[bond_data](bond_data)  -绿色债券相关dataset

[assets](assets)    -web图片dataset

[backend_api.py](backend_api.py)    -（新增）fastapi后端

[FRONTEND_API_MAPPING.md](FRONTEND_API_MAPPING.md)  -（新增）后端api说明表，供前端将api功能对其旧的streamlit_web

[rework_oil_price_prediction.py](rework_oil_price_prediction.py)    -（新增）预测模型修改，结果在rework_result

[noise_binary_test.py](noise_binary_test.py)    -(新增)检查新模型是否可行

[rework_result](rework_result)  -（新增）新模型结果存储

[rework_Vue](rework_Vue)    -（新增）新前端

[wti_gru_sequence.py](wti_gru_sequence.py)  -reworkmodel 建模

[wti_live_predict.py](wti_live_predict.py)  -reworkmodel 实盘

[optuna_best_params_full.json](optuna_best_params_full.json)    -wti_gru用的配置json

启动命令：
web :streamlit run streamlit_app_0325.py
oilprice :python oil_price_prediction_main_0309.py
fastapi:uvicorn backend_api:app --host 127.0.0.1 --port 8000 --reload

网址：http://47.110.235.34:8501

fastapi联调总控页：http://127.0.0.1:8000/docs#/

