#!/usr/bin/env python3

def bits_to_kb(bits):
    return bits / 8 / 1024

def calculate_gshare_memory(history_bits):
    """计算Gshare预测器内存使用"""
    pht_bits = (2 ** history_bits) * 2
    global_history_bits = history_bits
    total_bits = pht_bits + global_history_bits
    
    return {
        'name': f'Gshare ({history_bits}-bit)',
        'pht_bits': pht_bits,
        'global_history_bits': global_history_bits,
        'total_bits': total_bits,
        'total_kb': bits_to_kb(total_bits)
    }

def calculate_tournament_memory(global_bits, local_bits, index_bits):
    """计算Tournament预测器内存使用"""
    global_pht_bits = (2 ** global_bits) * 2
    local_history_bits = (2 ** index_bits) * local_bits
    local_pht_bits = (2 ** local_bits) * 2
    choice_pht_bits = (2 ** global_bits) * 2
    global_history_reg_bits = global_bits
    
    total_bits = (global_pht_bits + local_history_bits + local_pht_bits + 
                 choice_pht_bits + global_history_reg_bits)
    
    return {
        'name': f'Tournament ({global_bits}:{local_bits}:{index_bits})',
        'global_pht_bits': global_pht_bits,
        'local_history_bits': local_history_bits,
        'local_pht_bits': local_pht_bits,
        'choice_pht_bits': choice_pht_bits,
        'global_history_reg_bits': global_history_reg_bits,
        'total_bits': total_bits,
        'total_kb': bits_to_kb(total_bits)
    }

def calculate_advanced_custom_memory():
    """计算高级Custom预测器内存使用"""
    # 配置参数
    CUSTOM_GSHARE_BITS = 14      # 16K entries
    CUSTOM_BIMODAL_BITS = 13     # 8K entries  
    CUSTOM_PATH_BITS = 12        # 4K entries
    CUSTOM_META_BITS = 12        # 4K entries
    CUSTOM_HISTORY_LENGTH = 14   # 14位历史
    
    # 各组件内存计算
    gshare_table_bits = (2 ** CUSTOM_GSHARE_BITS) * 2
    bimodal_table_bits = (2 ** CUSTOM_BIMODAL_BITS) * 2
    path_table_bits = (2 ** CUSTOM_PATH_BITS) * 2
    meta_table_bits = (2 ** CUSTOM_META_BITS) * 2
    
    # 历史寄存器
    global_history_bits = CUSTOM_HISTORY_LENGTH
    path_history_bits = CUSTOM_HISTORY_LENGTH
    
    total_bits = (gshare_table_bits + bimodal_table_bits + path_table_bits + 
                 meta_table_bits + global_history_bits + path_history_bits)
    
    return {
        'name': f'Custom Advanced (G{CUSTOM_GSHARE_BITS}+B{CUSTOM_BIMODAL_BITS}+P{CUSTOM_PATH_BITS}+M{CUSTOM_META_BITS})',
        'gshare_table_bits': gshare_table_bits,
        'bimodal_table_bits': bimodal_table_bits,
        'path_table_bits': path_table_bits,
        'meta_table_bits': meta_table_bits,
        'global_history_bits': global_history_bits,
        'path_history_bits': path_history_bits,
        'total_bits': total_bits,
        'total_kb': bits_to_kb(total_bits),
        'components': [
            f'Gshare Table: {2**CUSTOM_GSHARE_BITS:,} entries × 2 bits = {gshare_table_bits:,} bits',
            f'Bimodal Table: {2**CUSTOM_BIMODAL_BITS:,} entries × 2 bits = {bimodal_table_bits:,} bits',
            f'Path Table: {2**CUSTOM_PATH_BITS:,} entries × 2 bits = {path_table_bits:,} bits',
            f'Meta Table: {2**CUSTOM_META_BITS:,} entries × 2 bits = {meta_table_bits:,} bits',
            f'Global History: {global_history_bits} bits',
            f'Path History: {path_history_bits} bits'
        ]
    }

def calculate_optimized_custom_memory():
    """计算优化版Custom预测器内存使用（针对最后一个trace）"""
    # 更激进的配置
    CUSTOM_GSHARE_BITS = 15      # 32K entries
    CUSTOM_BIMODAL_BITS = 14     # 16K entries  
    CUSTOM_PATH_BITS = 13        # 8K entries
    CUSTOM_META_BITS = 13        # 8K entries
    CUSTOM_HISTORY_LENGTH = 16   # 16位历史
    
    gshare_table_bits = (2 ** CUSTOM_GSHARE_BITS) * 2
    bimodal_table_bits = (2 ** CUSTOM_BIMODAL_BITS) * 2
    path_table_bits = (2 ** CUSTOM_PATH_BITS) * 2
    meta_table_bits = (2 ** CUSTOM_META_BITS) * 2
    global_history_bits = CUSTOM_HISTORY_LENGTH
    path_history_bits = CUSTOM_HISTORY_LENGTH
    
    total_bits = (gshare_table_bits + bimodal_table_bits + path_table_bits + 
                 meta_table_bits + global_history_bits + path_history_bits)
    
    return {
        'name': f'Custom Optimized (G{CUSTOM_GSHARE_BITS}+B{CUSTOM_BIMODAL_BITS}+P{CUSTOM_PATH_BITS}+M{CUSTOM_META_BITS})',
        'gshare_table_bits': gshare_table_bits,
        'bimodal_table_bits': bimodal_table_bits,
        'path_table_bits': path_table_bits,
        'meta_table_bits': meta_table_bits,
        'global_history_bits': global_history_bits,
        'path_history_bits': path_history_bits,
        'total_bits': total_bits,
        'total_kb': bits_to_kb(total_bits),
        'components': [
            f'Gshare Table: {2**CUSTOM_GSHARE_BITS:,} entries × 2 bits = {gshare_table_bits:,} bits',
            f'Bimodal Table: {2**CUSTOM_BIMODAL_BITS:,} entries × 2 bits = {bimodal_table_bits:,} bits',
            f'Path Table: {2**CUSTOM_PATH_BITS:,} entries × 2 bits = {path_table_bits:,} bits',
            f'Meta Table: {2**CUSTOM_META_BITS:,} entries × 2 bits = {meta_table_bits:,} bits',
            f'Global History: {global_history_bits} bits',
            f'Path History: {path_history_bits} bits'
        ]
    }

def print_memory_analysis():
    """打印完整的内存使用分析"""
    print("=" * 80)
    print("UPDATED BRANCH PREDICTOR MEMORY USAGE ANALYSIS")
    print("=" * 80)
    
    # 内存限制
    max_memory_bits = 64 * 1024 * 8 + 256  # 64KB + 256 bits
    max_memory_kb = bits_to_kb(max_memory_bits)
    
    print(f"\nMemory Constraint: {max_memory_bits:,} bits = {max_memory_kb:.2f} KB")
    print("=" * 80)
    
    # 计算所有预测器的内存使用
    predictors = [
        calculate_gshare_memory(13),
        calculate_tournament_memory(9, 10, 10),
        calculate_advanced_custom_memory(),
        calculate_optimized_custom_memory()
    ]
    
    # 详细分析每个预测器
    for i, pred in enumerate(predictors, 1):
        print(f"\n{i}. {pred['name']}")
        print("-" * 60)
        
        # 打印组件详情
        if 'components' in pred:
            for comp in pred['components']:
                print(f"   {comp}")
        else:
            # 简单预测器的输出
            for key, value in pred.items():
                if key.endswith('_bits') and key != 'total_bits':
                    component_name = key.replace('_bits', '').replace('_', ' ').title()
                    print(f"   {component_name}: {value:,} bits")
        
        # 总计和状态检查
        usage_percent = (pred['total_bits'] / max_memory_bits) * 100
        status = "✓ PASS" if pred['total_bits'] <= max_memory_bits else "✗ EXCEED"
        
        print(f"   {'='*50}")
        print(f"   Total: {pred['total_bits']:,} bits = {pred['total_kb']:.3f} KB")
        print(f"   Usage: {usage_percent:.2f}% of limit {status}")
        
        if pred['total_bits'] > max_memory_bits:
            excess_kb = bits_to_kb(pred['total_bits'] - max_memory_bits)
            print(f"   ⚠️  EXCEEDS LIMIT BY {excess_kb:.3f} KB")
    
    # 汇总表格
    print(f"\n{'='*80}")
    print("MEMORY USAGE SUMMARY TABLE")
    print("=" * 80)
    print(f"{'Predictor':<35} {'Memory (KB)':<12} {'Memory (%)':<12} {'Status':<8}")
    print("-" * 80)
    
    for pred in predictors:
        usage_percent = (pred['total_bits'] / max_memory_bits) * 100
        status = "✓ PASS" if pred['total_bits'] <= max_memory_bits else "✗ EXCEED"
        print(f"{pred['name']:<35} {pred['total_kb']:<12.3f} {usage_percent:<12.2f} {status:<8}")
    
    # 优化建议
    print(f"\n{'='*80}")
    print("OPTIMIZATION ANALYSIS")
    print("=" * 80)
    
    advanced_custom = predictors[2]
    optimized_custom = predictors[3]
    
    print(f"\nCurrent Advanced Custom Predictor:")
    print(f"  Memory usage: {advanced_custom['total_kb']:.3f} KB ({(advanced_custom['total_bits']/max_memory_bits)*100:.1f}%)")
    
    print(f"\nOptimized Custom Predictor (for last trace):")
    print(f"  Memory usage: {optimized_custom['total_kb']:.3f} KB ({(optimized_custom['total_bits']/max_memory_bits)*100:.1f}%)")
    
    if optimized_custom['total_bits'] <= max_memory_bits:
        remaining_bits = max_memory_bits - optimized_custom['total_bits']
        remaining_kb = bits_to_kb(remaining_bits)
        print(f"  ✅ Still within memory limit!")
        print(f"  🆓 Remaining: {remaining_kb:.3f} KB")
    else:
        excess_kb = bits_to_kb(optimized_custom['total_bits'] - max_memory_bits)
        print(f"  ❌ Exceeds limit by {excess_kb:.3f} KB")

if __name__ == "__main__":
    calculate_memory_usage()
