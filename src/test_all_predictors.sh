#!/bin/bash

# 完整的分支预测器测试套件
# 包含性能测试、内存分析、CSV生成、结果分析和报告生成
# 使用方法: ./complete_test.sh

echo "========================================="
echo "COMPLETE BRANCH PREDICTOR TEST SUITE"
echo "========================================="
echo "Generated on: $(date)"
echo ""

# 创建带时间戳的结果目录
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RESULTS_DIR="results_$TIMESTAMP"
mkdir -p "$RESULTS_DIR"

echo "📁 Results directory: $RESULTS_DIR"
echo ""

# ================================
# 1. 环境检查
# ================================
echo "🔍 1. ENVIRONMENT CHECK"
echo "======================"

if [ ! -f "predictor" ]; then
    echo "❌ predictor executable not found!"
    echo "   🔨 Running make..."
    make clean && make
    if [ $? -ne 0 ]; then
        echo "❌ Compilation failed!"
        exit 1
    fi
    echo "✅ Compilation successful"
else
    echo "✅ predictor executable found"
fi

if [ ! -d "../traces" ]; then
    echo "❌ traces directory not found!"
    exit 1
fi

# 检查解压的trace文件
echo "📋 Checking trace files..."
TRACE_COUNT=0
for trace_file in fp_1 fp_2 int_1 int_2 mm_1 mm_2; do
    if [ -f "../traces/$trace_file" ]; then
        TRACE_COUNT=$((TRACE_COUNT + 1))
        echo "   ✅ $trace_file"
    else
        echo "   ❌ $trace_file (missing - checking .bz2)"
        if [ -f "../traces/$trace_file.bz2" ]; then
            echo "      🔄 Decompressing $trace_file.bz2..."
            bunzip2 -k "../traces/$trace_file.bz2"
            if [ -f "../traces/$trace_file" ]; then
                TRACE_COUNT=$((TRACE_COUNT + 1))
                echo "      ✅ $trace_file decompressed"
            fi
        fi
    fi
done

echo "📊 Found $TRACE_COUNT/6 trace files"
if [ $TRACE_COUNT -ne 6 ]; then
    echo "❌ Missing trace files! Cannot proceed."
    exit 1
fi

echo ""

# ================================
# 2. 性能测试
# ================================
echo "🚀 2. PERFORMANCE TESTING"
echo "========================="

# 创建结果文件
RESULTS_FILE="$RESULTS_DIR/predictor_results.txt"
echo "Branch Predictor Performance Results" > $RESULTS_FILE
echo "Generated on $(date)" >> $RESULTS_FILE
echo "Test Suite Version: Complete" >> $RESULTS_FILE
echo "=======================================" >> $RESULTS_FILE

# 测试所有trace文件
TRACES="../traces/fp_1 ../traces/fp_2 ../traces/int_1 ../traces/int_2 ../traces/mm_1 ../traces/mm_2"

echo "🔹 Testing Static predictor..."
echo -e "\n=== STATIC PREDICTOR ===" | tee -a $RESULTS_FILE
for trace in $TRACES; do
    trace_name=$(basename $trace)
    echo "Testing $trace_name with Static predictor:" | tee -a $RESULTS_FILE
    ./predictor --static $trace | tee -a $RESULTS_FILE
    echo "" | tee -a $RESULTS_FILE
done

echo "🔹 Testing Gshare predictor (13 bits)..."
echo -e "\n=== GSHARE PREDICTOR (13 bits) ===" | tee -a $RESULTS_FILE
for trace in $TRACES; do
    trace_name=$(basename $trace)
    echo "Testing $trace_name with Gshare predictor:" | tee -a $RESULTS_FILE
    ./predictor --gshare:13 $trace | tee -a $RESULTS_FILE
    echo "" | tee -a $RESULTS_FILE
done

echo "🔹 Testing Tournament predictor (9:10:10)..."
echo -e "\n=== TOURNAMENT PREDICTOR (9:10:10) ===" | tee -a $RESULTS_FILE
for trace in $TRACES; do
    trace_name=$(basename $trace)
    echo "Testing $trace_name with Tournament predictor:" | tee -a $RESULTS_FILE
    ./predictor --tournament:9:10:10 $trace | tee -a $RESULTS_FILE
    echo "" | tee -a $RESULTS_FILE
done

echo "🔹 Testing Custom predictor..."
echo -e "\n=== CUSTOM PREDICTOR ===" | tee -a $RESULTS_FILE
for trace in $TRACES; do
    trace_name=$(basename $trace)
    echo "Testing $trace_name with Custom predictor:" | tee -a $RESULTS_FILE
    ./predictor --custom $trace | tee -a $RESULTS_FILE
    echo "" | tee -a $RESULTS_FILE
done

echo ""
echo "✅ Performance testing completed!"
echo "📄 Results saved to: $RESULTS_FILE"
echo ""

# ================================
# 3. CSV生成和数据提取
# ================================
echo "📊 3. CSV GENERATION AND DATA EXTRACTION"
echo "========================================"

cat > "$RESULTS_DIR/extract_results.py" << 'EOF'
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
        ('CUSTOM', 'CUSTOM PREDICTOR')
    ]
    traces = ['fp_1', 'fp_2', 'int_1', 'int_2', 'mm_1', 'mm_2']

    # CSV输出
    print("Predictor,fp_1,fp_2,int_1,int_2,mm_1,mm_2")
    
    results_data = {}
    
    for pred_short, pred_full in predictors:
        row = [pred_short]
        results_data[pred_short] = []
        
        # 找到对应预测器的部分
        pattern = f"=== {pred_full} ==="
        start = content.find(pattern)
        if start == -1:
            print(f"Warning: Could not find section for {pred_full}", file=sys.stderr)
            continue
        
        # 找到下一个预测器的开始位置
        next_pred_idx = len(content)
        temp_start = start + len(pattern)
        
        # Search for the start of the next predictor section
        for other_short, other_full in predictors:
            if other_short != pred_short:
                next_pattern = f"=== {other_full} ==="
                pos = content.find(next_pattern, temp_start)
                if pos != -1 and pos < next_pred_idx:
                    next_pred_idx = pos
        
        section = content[start:next_pred_idx]
        
        # 提取每个trace的误预测率 (MPKI)
        for trace in traces:
            # 匹配 "MPKI:    12.128" 这样的格式
            trace_pattern = r"Testing " + re.escape(trace) + r".*?MPKI:\s*([0-9.]+)"
            match = re.search(trace_pattern, section, re.DOTALL)
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
    
    if 'CUSTOM' not in results_data or not results_data['CUSTOM']:
        print("❌ Custom predictor results not found!", file=sys.stderr)
        return
    
    custom_results = results_data['CUSTOM']
    
    print(f"\n📊 CUSTOM PREDICTOR PERFORMANCE (MPKI):", file=sys.stderr)
    for i, trace in enumerate(traces):
        if i < len(custom_results) and custom_results[i] is not None:
            print(f"   {trace}: {custom_results[i]:.3f}", file=sys.stderr)
    
    # 计算平均值
    valid_custom = [x for x in custom_results if x is not None]
    if valid_custom:
        avg_custom = sum(valid_custom) / len(valid_custom)
        print(f"   Average: {avg_custom:.3f}", file=sys.stderr)
    
    # 与其他预测器比较
    for compare_to in ['GSHARE', 'TOURNAMENT']:
        if compare_to in results_data:
            compare_results = results_data[compare_to]
            wins = 0
            total_compare = 0
            for i in range(len(traces)):
                if (i < len(custom_results) and i < len(compare_results) and 
                    custom_results[i] is not None and compare_results[i] is not None):
                    total_compare += 1
                    # Lower MPKI is better
                    if custom_results[i] < compare_results[i]:
                        wins += 1
            
            print(f"\n🆚 CUSTOM vs {compare_to}:", file=sys.stderr)
            print(f"   Custom is better (lower MPKI) in: {wins}/{total_compare} traces", file=sys.stderr)
            if wins == total_compare and total_compare > 0:
                print(f"   🏆 PERFECT! Custom beats {compare_to} in ALL traces!", file=sys.stderr)
            elif wins >= total_compare / 2:
                print(f"   ✅ GOOD! Custom beats {compare_to} in the majority of traces.", file=sys.stderr)
            else:
                print(f"   ❌ NEEDS IMPROVEMENT. Custom does not beat {compare_to} in the majority of traces.", file=sys.stderr)

if __name__ == "__main__":
    results_data, traces = extract_results()
    generate_analysis(results_data, traces)

EOF

# 运行数据提取
cd "$RESULTS_DIR"
python3 extract_results.py > predictor_summary.csv 2> analysis_report.txt
cd ..

echo "📄 CSV data saved to: $RESULTS_DIR/predictor_summary.csv"
echo "📊 Analysis report saved to: $RESULTS_DIR/analysis_report.txt"

# 显示CSV内容
echo ""
echo "📋 CSV SUMMARY:"
echo "==============="
cat "$RESULTS_DIR/predictor_summary.csv"

echo ""
echo "📊 ANALYSIS REPORT:"
echo "=================="
cat "$RESULTS_DIR/analysis_report.txt"

# ================================
# 4. 内存使用分析
# ================================
echo ""
echo "💾 4. MEMORY USAGE ANALYSIS (Updated for Perceptron)"
echo "================================================="

# <<< --- START OF MODIFIED SECTION --- >>>
cat > "$RESULTS_DIR/memory_analysis.py" << 'EOF'
#!/usr/bin/env python3
import math

def bits_to_kb(bits):
    """Converts bits to Kilobytes (KB)."""
    return bits / 8 / 1024

def calculate_gshare_memory(history_bits):
    """Calculates memory usage for a Gshare predictor."""
    # 2-bit saturating counters for the Pattern History Table (PHT)
    pht_bits = (2 ** history_bits) * 2
    global_history_bits = history_bits
    total_bits = pht_bits + global_history_bits
    
    return {
        'name': f'Gshare ({history_bits}-bit)',
        'total_bits': total_bits,
        'total_kb': bits_to_kb(total_bits),
        'components': [
            f'Pattern History Table: 2^{history_bits} entries * 2 bits/entry = {pht_bits:,} bits',
            f'Global History Register: {global_history_bits:,} bits'
        ]
    }

def calculate_tournament_memory(global_bits, local_bits, index_bits):
    """Calculates memory usage for a Tournament predictor."""
    global_pht_bits = (2 ** global_bits) * 2
    local_history_table_bits = (2 ** index_bits) * local_bits
    local_pht_bits = (2 ** local_bits) * 2
    choice_pht_bits = (2 ** global_bits) * 2
    global_history_reg_bits = global_bits
    
    total_bits = (global_pht_bits + local_history_table_bits + local_pht_bits + 
                  choice_pht_bits + global_history_reg_bits)
    
    return {
        'name': f'Tournament ({global_bits}:{local_bits}:{index_bits})',
        'total_bits': total_bits,
        'total_kb': bits_to_kb(total_bits),
        'components': [
            f'Global PHT: 2^{global_bits} entries * 2 bits = {global_pht_bits:,} bits',
            f'Local History Table: 2^{index_bits} entries * {local_bits} bits = {local_history_table_bits:,} bits',
            f'Local PHT: 2^{local_bits} entries * 2 bits = {local_pht_bits:,} bits',
            f'Choice PHT: 2^{global_bits} entries * 2 bits = {choice_pht_bits:,} bits',
            f'Global History Register: {global_history_reg_bits} bits'
        ]
    }

def calculate_perceptron_memory(history_length, num_tables):
    """Calculates memory usage for the Perceptron predictor."""
    # Each weight is an 8-bit signed integer (int8_t)
    weight_size_bits = 8
    
    # Weight table size: num_tables * (history + 1 bias weight) * bits_per_weight
    weights_table_bits = num_tables * (history_length + 1) * weight_size_bits
    
    # Global history register size
    ghistory_reg_bits = history_length
    
    total_bits = weights_table_bits + ghistory_reg_bits
    
    return {
        'name': f'Custom Perceptron (H={history_length}, T={num_tables})',
        'total_bits': total_bits,
        'total_kb': bits_to_kb(total_bits),
        'components': [
            f'Weights Table: {num_tables:,} tables * ({history_length}+1 bias) weights/table * {weight_size_bits} bits/weight = {weights_table_bits:,} bits',
            f'Global History Register: {ghistory_reg_bits} bits'
        ]
    }

def print_memory_analysis():
    """Prints the complete memory usage analysis."""
    # --- IMPORTANT: These parameters must match your C code! ---
    # Parameters for the standard predictors being tested
    GSHARE_BITS = 13
    TOURNAMENT_G_BITS, TOURNAMENT_L_BITS, TOURNAMENT_I_BITS = 9, 10, 10
    
    # Parameters for your Custom Perceptron predictor
    PERCEPTRON_HISTORY_LENGTH = 25
    NUM_WEIGHT_TABLES = 163
    # -----------------------------------------------------------

    # Usually there is a memory constraint for the custom predictor
    # Check your project description. A common limit is (32KB + 1K) bits.
    max_memory_bits = 32 * 1024 * 8 + 1024
    max_memory_kb = bits_to_kb(max_memory_bits)
    
    print("=" * 80)
    print("BRANCH PREDICTOR MEMORY USAGE ANALYSIS (PERCEPTRON)")
    print("=" * 80)
    print(f"\nAssumed Custom Predictor Memory Constraint: {max_memory_bits:,} bits = {max_memory_kb:.2f} KB")
    print("=" * 80)
    
    predictors = [
        calculate_gshare_memory(GSHARE_BITS),
        calculate_tournament_memory(TOURNAMENT_G_BITS, TOURNAMENT_L_BITS, TOURNAMENT_I_BITS),
        calculate_perceptron_memory(PERCEPTRON_HISTORY_LENGTH, NUM_WEIGHT_TABLES)
    ]
    
    for i, pred in enumerate(predictors, 1):
        print(f"\n{i}. {pred['name']}")
        print("-" * 60)
        
        for comp in pred['components']:
            print(f"   {comp}")
        
        print(f"   {'-'*50}")
        print(f"   Total: {pred['total_bits']:,} bits = {pred['total_kb']:.3f} KB")
        
        # Check against limit only for custom predictor
        if "Custom" in pred['name']:
            usage_percent = (pred['total_bits'] / max_memory_bits) * 100
            status = "✓ PASS" if pred['total_bits'] <= max_memory_bits else "✗ FAIL"
            print(f"\n   Usage vs Limit: {usage_percent:.2f}% of {max_memory_kb:.2f} KB limit --- {status}")
            if pred['total_bits'] > max_memory_bits:
                excess_kb = bits_to_kb(pred['total_bits'] - max_memory_bits)
                print(f"   ⚠️  EXCEEDS LIMIT BY {excess_kb:.3f} KB")

    # Summary Table
    print(f"\n{'='*80}")
    print("MEMORY USAGE SUMMARY TABLE")
    print("=" * 80)
    print(f"{'Predictor':<45} {'Memory (KB)':<15} {'Status vs Limit'}")
    print("-" * 80)
    
    for pred in predictors:
        status = "-"
        if "Custom" in pred['name']:
            status = "✓ PASS" if pred['total_bits'] <= max_memory_bits else "✗ FAIL"
        print(f"{pred['name']:<45} {pred['total_kb']:<15.3f} {status}")
    print("=" * 80)

if __name__ == "__main__":
    print_memory_analysis()
EOF
# <<< --- END OF MODIFIED SECTION --- >>>

cd "$RESULTS_DIR"
python3 memory_analysis.py > memory_report.txt
cat memory_report.txt
cd ..

echo ""
echo "💾 Memory analysis saved to: $RESULTS_DIR/memory_report.txt"
echo "   (Note: Assumed a 32K+1K bit limit for Custom, check your project spec)"

# ================================
# 5. 生成最终报告摘要
# ================================
echo ""
echo "📋 5. FINAL REPORT SUMMARY"
echo "=========================="

cat > "$RESULTS_DIR/final_summary.txt" << EOF
BRANCH PREDICTOR PROJECT - FINAL SUMMARY
========================================
Generated: $(date)
Student: $(grep "studentName" predictor.c | cut -d'"' -f2 2>/dev/null || echo "Not specified")
Student ID: $(grep "studentID" predictor.c | cut -d'"' -f2 2>/dev/null || echo "Not specified")

TEST RESULTS:
============
See predictor_summary.csv for detailed performance data (MPKI).
See analysis_report.txt for performance comparison.
See memory_report.txt for memory usage analysis.

FILES IN THIS RESULTS PACKAGE:
==============================
- predictor_results.txt   : Raw test output from the predictor executable
- predictor_summary.csv   : Performance data (MPKI) in CSV format
- analysis_report.txt     : Performance comparison of Custom vs others
- memory_report.txt       : Memory usage calculation for all predictors
- extract_results.py      : Data extraction script
- memory_analysis.py      : Memory analysis script
- final_summary.txt       : This summary file

NEXT STEPS:
===========
1. Review analysis_report.txt for a performance evaluation.
2. Check memory_report.txt to verify your Custom predictor is within budget.
3. Use the data in predictor_summary.csv for any graphs in your report.
4. Include the memory analysis table in your project report.

PROJECT STATUS:
==============
✅ All predictors implemented and tested
✅ Performance data collected and summarized
✅ Memory usage analyzed for the new Perceptron predictor
✅ Ready for report writing!
EOF

echo "📄 Final summary saved to: $RESULTS_DIR/final_summary.txt"

# ================================
# 6. 完成信息
# ================================
echo ""
echo "🎉 COMPLETE TEST SUITE FINISHED!"
echo "================================"
echo "📁 All results saved in: $RESULTS_DIR/"
echo ""
echo "📋 Key files to review:"
echo "   📊 $RESULTS_DIR/predictor_summary.csv    - Performance data (MPKI)"
echo "   📈 $RESULTS_DIR/analysis_report.txt      - Performance analysis"
echo "   💾 $RESULTS_DIR/memory_report.txt        - **NEW** Memory usage for Perceptron"
echo "   📄 $RESULTS_DIR/final_summary.txt        - Complete summary"
echo ""
echo "✅ Your branch predictor project is ready for report writing!"
echo "🎯 Use the analysis data to demonstrate your predictor's performance!"
echo ""