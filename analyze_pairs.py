from stock_ratio import analyze_stock_ratio
import time

def analyze_multiple_pairs(pairs, period='6mo'):
    """
    Analyze multiple pairs of stocks
    
    Parameters:
    -----------
    pairs : list of tuples
        List of (target_stock, base_stock) pairs to analyze
    period : str, optional
        The time period for analysis (default: '6mo')
    """
    results = {}
    
    for target, base in pairs:
        print("\n" + "="*50)
        print(f"Analyzing {target} relative to {base}")
        print("="*50)
        
        # Perform analysis
        result = analyze_stock_ratio(target, base, period)
        if result:
            results[(target, base)] = result
            
        # Add a small delay between analyses to avoid rate limiting
        time.sleep(2)
    
    return results

def main():
    # Define the pairs to analyze
    pairs = [
        ("NVDA", "SOXX"),    # NVIDIA vs Semiconductor ETF
        ("TSLA", "QQQ"),     # Tesla vs Nasdaq 100 ETF
        ("GOOGL", "QQQ")     # Google vs Nasdaq 100 ETF
    ]
    
    # Perform analysis
    results = analyze_multiple_pairs(pairs)
    
    # Print summary
    print("\n" + "="*50)
    print("SUMMARY OF ALL ANALYSES")
    print("="*50)
    
    for (target, base), result in results.items():
        print(f"\n{target} vs {base}:")
        print(f"Beta: {result['beta']:.2f}")
        print(f"Expected Drop (if {base} drops 5%): {result['expected_drop_5pct']:.2%}")
        print(f"Correlation: {result['correlation']:.2f}")
        print(f"Information Ratio: {result['information_ratio']:.2f}")
        print("-"*30)

if __name__ == "__main__":
    main() 