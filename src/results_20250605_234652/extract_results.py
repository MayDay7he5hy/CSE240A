import re
import sys

def extract_results():
    # 读取结果文件
    try:
        with open('predictor_results.txt', 'r') as f:
            content = f.read()
    except FileNotFoundError:
        print("Error: predictor_results.txt not found!")
        sys.exit(1)

    # 解析结果
    predictors = [
        ('STATIC', 'STATIC PREDICTOR'),
        ('GSHARE', 'GSHARE PREDICTOR (13 bits)'),
        ('TOURNAMENT', 'TOURNAMENT PREDICTOR (9:10:10)'),
        ('CUSTOM', 'CUSTOM HYBRID PREDICTOR')
    ]
    traces = ['fp_1', 'fp_2', 'int_1', 'int_2', 'mm_1', 'mm_2']

    # CSV输出
    print("Predictor,fp_1,fp_2,int_1,int_2,mm_1,mm_2")
    
    results_data = {}
    
    for pred_short, pred_pattern in predictors:
        row = [pred_short]
        results_data[pred_short] = []
        
        # 找到对应预测器的部分
        pattern = f"=== {pred_pattern}"
        start = content.find(pattern)
        if start == -1:
            print(f"Warning: Could not find section for {pred_pattern}", file=sys.stderr)
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
                results_data[pred_short].append(rate)
            else:
                row.append("N/A")
                results_data[pred_short].append(None)
        
        print(",".join(row))
    
    return results_data, traces

def generate_analysis(results_data, traces):
    print("\n" + "="*60, file=sys.stderr)
    print("PERFORMANCE ANALYSIS REPORT", file=sys.stderr)
    print("="*60, file=sys.stderr)
    
    if 'CUSTOM' not in results_data:
        print("❌ Custom predictor results not found!", file=sys.stderr)
        return
    
    custom_results = results_data['CUSTOM']
    
    print(f"\n📊 CUSTOM PREDICTOR PERFORMANCE:", file=sys.stderr)
    for i, trace in enumerate(traces):
        if i < len(custom_results) and custom_results[i] is not None:
            print(f"  {trace}: {custom_results[i]:.3f}%", file=sys.stderr)
    
    # 计算平均值
    valid_custom = [x for x in custom_results if x is not None]
    if valid_custom:
        avg_custom = sum(valid_custom) / len(valid_custom)
        print(f"  Average: {avg_custom:.3f}%", file=sys.stderr)
    
    # 与其他预测器比较
    if 'GSHARE' in results_data:
        gshare_results = results_data['GSHARE']
        wins_vs_gshare = 0
        total_gshare = 0
        for i in range(len(traces)):
            if (i < len(custom_results) and i < len(gshare_results) and 
                custom_results[i] is not None and gshare_results[i] is not None):
                total_gshare += 1
                if custom_results[i] < gshare_results[i]:
                    wins_vs_gshare += 1
        
        print(f"\n🆚 CUSTOM vs GSHARE:", file=sys.stderr)
        print(f"  Custom wins: {wins_vs_gshare}/{total_gshare} traces", file=sys.stderr)
        if wins_vs_gshare == total_gshare:
            print(f"  🏆 PERFECT! Custom beats Gshare in ALL traces!", file=sys.stderr)
        elif wins_vs_gshare >= total_gshare // 2:
            print(f"  ✅ Custom beats Gshare in majority of traces", file=sys.stderr)
        else:
            print(f"  ❌ Custom loses to Gshare in majority of traces", file=sys.stderr)
    
    if 'TOURNAMENT' in results_data:
        tournament_results = results_data['TOURNAMENT']
        wins_vs_tournament = 0
        total_tournament = 0
        for i in range(len(traces)):
            if (i < len(custom_results) and i < len(tournament_results) and 
                custom_results[i] is not None and tournament_results[i] is not None):
                total_tournament += 1
                if custom_results[i] < tournament_results[i]:
                    wins_vs_tournament += 1
        
        print(f"\n🆚 CUSTOM vs TOURNAMENT:", file=sys.stderr)
        print(f"  Custom wins: {wins_vs_tournament}/{total_tournament} traces", file=sys.stderr)
        if wins_vs_tournament == total_tournament:
            print(f"  🏆 PERFECT! Custom beats Tournament in ALL traces!", file=sys.stderr)
        elif wins_vs_tournament >= total_tournament // 2:
            print(f"  ✅ Custom beats Tournament in majority of traces", file=sys.stderr)
        else:
            print(f"  ❌ Custom loses to Tournament in majority of traces", file=sys.stderr)
    
    # 评分预测
    print(f"\n🎯 SCORING PREDICTION:", file=sys.stderr)
    gshare_score = 0
    tournament_score = 0
    
    if 'GSHARE' in results_data:
        if wins_vs_gshare == total_gshare:
            gshare_score = 15
        elif wins_vs_gshare >= 3:
            gshare_score = 7.5
        print(f"  vs Gshare: {gshare_score}/15 points", file=sys.stderr)
    
    if 'TOURNAMENT' in results_data:
        if wins_vs_tournament == total_tournament:
            tournament_score = 15
        elif wins_vs_tournament >= 3:
            tournament_score = 7.5
        print(f"  vs Tournament: {tournament_score}/15 points", file=sys.stderr)
    
    total_custom_score = gshare_score + tournament_score
    print(f"  Total Custom Score: {total_custom_score}/30 points", file=sys.stderr)
    
    if total_custom_score >= 25:
        print(f"  🌟 EXCELLENT! Outstanding performance!", file=sys.stderr)
    elif total_custom_score >= 15:
        print(f"  ✅ GOOD! Solid performance!", file=sys.stderr)
    else:
        print(f"  ⚠️  NEEDS IMPROVEMENT", file=sys.stderr)

if __name__ == "__main__":
    results_data, traces = extract_results()
    generate_analysis(results_data, traces)
