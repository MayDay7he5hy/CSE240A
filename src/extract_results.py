import re
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

# 读取结果文件
with open('predictor_results.txt', 'r') as f:
    content = f.read()

# 解析结果
predictors = [
    ('STATIC', 'STATIC PREDICTOR'),
    ('GSHARE', 'GSHARE PREDICTOR'),
    ('TOURNAMENT', 'TOURNAMENT PREDICTOR'),
    ('CUSTOM', 'CUSTOM HYBRID PREDICTOR')
]
traces = ['fp_1', 'fp_2', 'int_1', 'int_2', 'mm_1', 'mm_2']

# 创建数据字典
data = {}
csv_rows = []

print("Predictor,fp_1,fp_2,int_1,int_2,mm_1,mm_2")

for pred_short, pred_pattern in predictors:
    row = [pred_short]
    data[pred_short] = []
    
    # 找到对应预测器的部分
    pattern = f"=== {pred_pattern}"
    start = content.find(pattern)
    if start == -1:
        print(f"Warning: Could not find section for {pred_pattern}")
        continue
    
    # 找到下一个预测器的开始位置
    next_pred_idx = len(content)
    for _, other_pattern in predictors:
        if other_pattern != pred_pattern:
            next_pattern = f"=== {other_pattern}"
            pos = content.find(next_pattern, start + 1)
            if pos != -1 and pos < next_pred_idx:
                next_pred_idx = pos
    
    section = content[start:next_pred_idx]
    
    # 提取每个trace的误预测率
    for trace in traces:
        pattern = r"Testing " + trace + r".*?Misprediction Rate:\s*([0-9.]+)"
        match = re.search(pattern, section, re.DOTALL)
        if match:
            rate = float(match.group(1))
            row.append(f"{rate:.3f}")
            data[pred_short].append(rate)
        else:
            row.append("N/A")
            data[pred_short].append(0)
    
    csv_rows.append(row)
    print(",".join(row))

# 保存CSV文件
with open('predictor_summary.csv', 'w') as f:
    f.write("Predictor,fp_1,fp_2,int_1,int_2,mm_1,mm_2\n")
    for row in csv_rows:
        f.write(",".join(row) + "\n")

# 创建性能对比图
plt.figure(figsize=(15, 10))

# 子图1: 所有预测器对比（柱状图）
plt.subplot(2, 2, 1)
x = np.arange(len(traces))
width = 0.2

for i, (pred_short, _) in enumerate(predictors):
    if pred_short in data:
        plt.bar(x + i*width, data[pred_short], width, label=pred_short)

plt.xlabel('Trace Files')
plt.ylabel('Misprediction Rate (%)')
plt.title('Branch Predictor Performance Comparison')
plt.xticks(x + width*1.5, traces)
plt.legend()
plt.grid(True, alpha=0.3)

# 子图2: 只比较智能预测器（去除Static）
plt.subplot(2, 2, 2)
smart_predictors = ['GSHARE', 'TOURNAMENT', 'CUSTOM']
for i, pred in enumerate(smart_predictors):
    if pred in data:
        plt.bar(x + i*width, data[pred], width, label=pred)

plt.xlabel('Trace Files')
plt.ylabel('Misprediction Rate (%)')
plt.title('Smart Predictors Comparison (Excluding Static)')
plt.xticks(x + width, traces)
plt.legend()
plt.grid(True, alpha=0.3)

# 子图3: Custom vs 其他预测器的改进百分比
plt.subplot(2, 2, 3)
if 'CUSTOM' in data and 'GSHARE' in data and 'TOURNAMENT' in data:
    gshare_improvement = [(g-c)/g*100 for g, c in zip(data['GSHARE'], data['CUSTOM'])]
    tournament_improvement = [(t-c)/t*100 for t, c in zip(data['TOURNAMENT'], data['CUSTOM'])]
    
    x = np.arange(len(traces))
    plt.bar(x - 0.2, gshare_improvement, 0.4, label='vs Gshare', alpha=0.7)
    plt.bar(x + 0.2, tournament_improvement, 0.4, label='vs Tournament', alpha=0.7)
    
    plt.xlabel('Trace Files')
    plt.ylabel('Improvement (%)')
    plt.title('Custom Predictor Improvement over Others')
    plt.xticks(x, traces)
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.axhline(y=0, color='black', linestyle='-', alpha=0.5)

# 子图4: 性能表格
plt.subplot(2, 2, 4)
plt.axis('off')

# 创建表格数据
table_data = []
for pred_short, _ in predictors:
    if pred_short in data:
        row = [pred_short] + [f"{x:.3f}%" for x in data[pred_short]]
        table_data.append(row)

table = plt.table(cellText=table_data,
                  colLabels=['Predictor'] + traces,
                  cellLoc='center',
                  loc='center',
                  bbox=[0, 0, 1, 1])

table.auto_set_font_size(False)
table.set_fontsize(8)
table.scale(1, 2)

# 设置表格样式
for i in range(len(predictors) + 1):
    for j in range(len(traces) + 1):
        cell = table[(i, j)]
        if i == 0:  # 标题行
            cell.set_facecolor('#40466e')
            cell.set_text_props(weight='bold', color='white')
        elif j == 0:  # 第一列
            cell.set_facecolor('#f1f1f2')
            cell.set_text_props(weight='bold')
        else:
            cell.set_facecolor('white')

plt.title('Detailed Performance Table', pad=20)

plt.tight_layout()
plt.savefig('predictor_performance.png', dpi=300, bbox_inches='tight')
plt.savefig('predictor_performance.pdf', bbox_inches='tight')

print("\nGraphs saved as:")
print("- predictor_performance.png")
print("- predictor_performance.pdf")

# 生成性能分析报告
print("\n" + "="*60)
print("PERFORMANCE ANALYSIS SUMMARY")
print("="*60)

if 'CUSTOM' in data:
    print("\nCustom Predictor Performance:")
    for i, trace in enumerate(traces):
        print(f"  {trace}: {data['CUSTOM'][i]:.3f}%")
    
    print(f"\nAverage Misprediction Rate: {np.mean(data['CUSTOM']):.3f}%")
    
    # 与其他预测器比较
    if 'GSHARE' in data:
        wins_vs_gshare = sum(1 for i in range(len(traces)) if data['CUSTOM'][i] < data['GSHARE'][i])
        print(f"Custom beats Gshare in {wins_vs_gshare}/{len(traces)} traces")
    
    if 'TOURNAMENT' in data:
        wins_vs_tournament = sum(1 for i in range(len(traces)) if data['CUSTOM'][i] < data['TOURNAMENT'][i])
        print(f"Custom beats Tournament in {wins_vs_tournament}/{len(traces)} traces")

print("\nDetailed CSV data saved to: predictor_summary.csv")
print("="*60)

