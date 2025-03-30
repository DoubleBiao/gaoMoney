from flask import Flask, render_template, request, jsonify
from models.portfolio_predictor import PortfolioPredictor
import json
from datetime import datetime
import os

app = Flask(__name__, 
    static_folder='static',
    template_folder='templates'
)

def get_portfolio_file_path():
    # 使用predictor目录下的portfolio.csv
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'portfolio.csv')

@app.route('/')
def index():
    try:
        # 从portfolio.csv读取初始数据
        portfolio_path = get_portfolio_file_path()
        if not os.path.exists(portfolio_path):
            raise FileNotFoundError(f"找不到portfolio.csv文件: {portfolio_path}")
            
        with open(portfolio_path, 'r') as f:
            portfolio_data = []
            # 跳过标题行
            next(f)
            for line in f:
                try:
                    symbol, shares, benchmark, adjustment, options = line.strip().split(',')
                    portfolio_data.append({
                        'symbol': symbol.strip(),
                        'shares': int(shares.strip()),
                        'benchmark': benchmark.strip(),
                        'adjustment': float(adjustment.strip()),
                        'options': int(options.strip()) if options.strip() else 0
                    })
                except ValueError as e:
                    print(f"解析行时出错: {line.strip()}")
                    print(f"错误信息: {str(e)}")
                    raise
                
        return render_template('index.html', 
                             portfolio=portfolio_data,
                             today='2025-04-17')
    except Exception as e:
        print(f"加载投资组合数据时出错: {str(e)}")
        return render_template('index.html', 
                             portfolio=[],
                             today='2025-04-17',
                             error=str(e))

@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.get_json()
        portfolio_data = data.get('portfolio_data', [])
        target_date = data.get('target_date')
        
        if not portfolio_data or not target_date:
            return jsonify({'error': '缺少必要的投资组合数据或目标日期'}), 400
            
        # 创建预测器实例并传入数据
        predictor = PortfolioPredictor(portfolio_data, target_date)
        result = predictor.predict()
        return jsonify(result)
    except Exception as e:
        print(f"预测过程中出错: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True) 