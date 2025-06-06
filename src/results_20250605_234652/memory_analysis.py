#!/usr/bin/env python3

def bits_to_kb(bits):
    return bits / 8 / 1024

def calculate_memory_usage():
    # 内存限制
    max_memory_bits = 64 * 1024 * 8 + 256  # 64KB + 256 bits
    max_memory_kb = bits_to_kb(max_memory_bits)
    
    print("MEMORY USAGE ANALYSIS")
    print("=" * 50)
    print(f"Memory Limit: {max_memory_bits:,} bits = {max_memory_kb:.3f} KB")
    print()
    
    # Gshare 13-bit
    gshare_pht_bits = (2**13) * 2  # 8192 entries × 2 bits
    gshare_history_bits = 13
    gshare_total = gshare_pht_bits + gshare_history_bits
    
    # Tournament 9:10:10
    tournament_global_pht = (2**9) * 2        # 512 entries × 2 bits
    tournament_local_history = (2**10) * 10   # 1024 entries × 10 bits
    tournament_local_pht = (2**10) * 2        # 1024 entries × 2 bits
    tournament_choice_pht = (2**9) * 2        # 512 entries × 2 bits
    tournament_global_history = 9
    tournament_total = (tournament_global_pht + tournament_local_history + 
                       tournament_local_pht + tournament_choice_pht + tournament_global_history)
    
    # Custom 14+13+12
    custom_gshare_pht = (2**14) * 2     # 16384 entries × 2 bits
    custom_bimodal_pht = (2**13) * 2    # 8192 entries × 2 bits
    custom_choice_pht = (2**12) * 2     # 4096 entries × 2 bits
    custom_global_history = 14
    custom_total = custom_gshare_pht + custom_bimodal_pht + custom_choice_pht + custom_global_history
    
    predictors = [
        ("Gshare (13-bit)", gshare_total),
        ("Tournament (9:10:10)", tournament_total),
        ("Custom (14+13+12)", custom_total)
    ]
    
    print("Predictor Memory Usage:")
    print("-" * 50)
    for name, bits in predictors:
        kb = bits_to_kb(bits)
        percent = (bits / max_memory_bits) * 100
        status = "✅ PASS" if bits <= max_memory_bits else "❌ EXCEED"
        print(f"{name:<20} {kb:8.3f} KB ({percent:5.1f}%) {status}")
    
    print()
    print("Detailed Breakdown:")
    print("-" * 50)
    
    print(f"Gshare (13-bit):")
    print(f"  PHT: {2**13:,} entries × 2 bits = {gshare_pht_bits:,} bits")
    print(f"  Global History: {gshare_history_bits} bits")
    print(f"  Total: {gshare_total:,} bits = {bits_to_kb(gshare_total):.3f} KB")
    print()
    
    print(f"Tournament (9:10:10):")
    print(f"  Global PHT: {2**9:,} entries × 2 bits = {tournament_global_pht:,} bits")
    print(f"  Local History: {2**10:,} entries × 10 bits = {tournament_local_history:,} bits")
    print(f"  Local PHT: {2**10:,} entries × 2 bits = {tournament_local_pht:,} bits")
    print(f"  Choice PHT: {2**9:,} entries × 2 bits = {tournament_choice_pht:,} bits")
    print(f"  Global History: {tournament_global_history} bits")
    print(f"  Total: {tournament_total:,} bits = {bits_to_kb(tournament_total):.3f} KB")
    print()
    
    print(f"Custom (14+13+12):")
    print(f"  Gshare PHT: {2**14:,} entries × 2 bits = {custom_gshare_pht:,} bits")
    print(f"  Bimodal PHT: {2**13:,} entries × 2 bits = {custom_bimodal_pht:,} bits")
    print(f"  Choice PHT: {2**12:,} entries × 2 bits = {custom_choice_pht:,} bits")
    print(f"  Global History: {custom_global_history} bits")
    print(f"  Total: {custom_total:,} bits = {bits_to_kb(custom_total):.3f} KB")
    print()
    
    # 验证内存约束
    custom_kb = bits_to_kb(custom_total)
    remaining_bits = max_memory_bits - custom_total
    remaining_kb = bits_to_kb(remaining_bits)
    
    print("Memory Constraint Verification:")
    print("-" * 50)
    if custom_total <= max_memory_bits:
        print(f"✅ Custom predictor fits within memory limit")
        print(f"📊 Used: {custom_kb:.3f} KB / {max_memory_kb:.3f} KB ({(custom_total/max_memory_bits)*100:.1f}%)")
        print(f"🆓 Remaining: {remaining_kb:.3f} KB")
        
        if remaining_kb > 4:
            print(f"💡 Optimization opportunity: Could use larger tables")
    else:
        excess_kb = bits_to_kb(custom_total - max_memory_bits)
        print(f"❌ Custom predictor exceeds memory limit by {excess_kb:.3f} KB")
        print(f"⚠️  Need to reduce table sizes")

if __name__ == "__main__":
    calculate_memory_usage()
