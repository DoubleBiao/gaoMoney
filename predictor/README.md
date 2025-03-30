# Portfolio Risk Predictor Web Application

这是一个基于 Flask 的投资组合风险预测 Web 应用。它允许用户动态调整投资组合参数，并实时查看风险预测结果。

## 功能特点

- 动态编辑投资组合参数（股票数量、基准指数、调整因子、期权数量）
- 实时更新风险预测
- 可视化展示预测结果
- 支持多个市场情景分析

## 安装步骤

1. 安装依赖：
```bash
pip install -r requirements.txt
```

2. 配置 E*TRADE API：
- 确保 `config.json` 文件包含有效的 API 凭证
- 文件格式：
```json
{
    "etrade": {
        "consumer_key": "YOUR_CONSUMER_KEY",
        "consumer_secret": "YOUR_CONSUMER_SECRET",
        "sandbox": false
    }
}
```

3. 准备投资组合数据：
- 在项目根目录创建 `portfolio.csv` 文件
- 包含以下列：symbol, shares, benchmark, adjustment, options

## 运行应用

```bash
python app.py
```

然后在浏览器中访问 `http://localhost:5000`

## 使用方法

1. 在网页界面中，你可以直接点击表格中的数值进行编辑
2. 选择预测日期
3. 点击 "Update Prediction" 按钮更新预测结果
4. 查看更新后的风险预测和情景分析

## 项目结构

```
predictor/
├── app.py              # Flask 应用主文件
├── requirements.txt    # 项目依赖
├── models/            # 预测模型
│   └── portfolio_predictor.py
├── static/            # 静态文件
├── templates/         # HTML 模板
│   └── index.html
└── README.md         # 项目文档
``` 