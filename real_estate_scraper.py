import pandas as pd
import os
from datetime import datetime

# ============================================================
# REAL ESTATE DATA ANALYZER - FINAL PERFECT VERSION
# Pandas 2.x compatible | Handles all edge cases
# Tools: Python, Pandas
# ============================================================

CITY_FILES = {
    'Delhi'     : 'Delhi.csv',
    'Mumbai'    : 'Mumbai.csv',
    'Bangalore' : 'Bangalore.csv',
    'Chennai'   : 'Chennai.csv',
    'Hyderabad' : 'Hyderabad.csv',
    'Kolkata'   : 'Kolkata.csv',
}

OUTPUT_FOLDER = 'output'
MASTER_FILE   = 'real_estate_all_cities.csv'
REPORT_FILE   = 'analysis_report.txt'
SUMMARY_FILE  = 'city_summary.csv'


def setup():
    """Create output folder if missing"""
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    print(f"Output folder ready: {OUTPUT_FOLDER}/")


def load_all_cities():
    """Load and combine all city CSV files"""
    all_data = []
    print("\n" + "="*60)
    print("STEP 1: LOADING DATA")
    print("="*60)

    for city, filename in CITY_FILES.items():
        if os.path.exists(filename):
            try:
                df = pd.read_csv(filename)
                df['City'] = city
                all_data.append(df)
                print(f"  [OK]   {city:12} : {len(df):>6,} records")
            except Exception as e:
                print(f"  [FAIL] {city:12} : {e}")
        else:
            print(f"  [SKIP] {city:12} : file not found")

    if not all_data:
        print("\nERROR: No CSV files loaded. Script stopped.")
        return None

    combined = pd.concat(all_data, ignore_index=True)
    print(f"\n  TOTAL : {len(combined):,} records across {len(all_data)} cities")
    return combined


def clean_data(df):
    """Clean the combined dataset safely"""
    print("\n" + "="*60)
    print("STEP 2: CLEANING DATA")
    print("="*60)
    before = len(df)

    # Remove fully empty rows and duplicates
    df = df.dropna(how='all')
    df = df.drop_duplicates()

    # Strip whitespace from text columns
    for col in df.select_dtypes(include='object').columns:
        df[col] = df[col].astype(str).str.strip()
        df[col] = df[col].replace({'nan': pd.NA, 'None': pd.NA, '': pd.NA})

    # Safely convert numeric-like columns (Pandas 2.x compatible)
    numeric_keywords = ['price', 'area', 'sqft', 'bhk', 'bedroom', 'bathroom']
    for col in df.columns:
        if col == 'City':
            continue
        if any(kw in col.lower() for kw in numeric_keywords):
            try:
                converted = pd.to_numeric(df[col], errors='coerce')
                # Only replace if at least 50% convert successfully
                if converted.notna().sum() > len(df) * 0.5:
                    df[col] = converted
            except Exception:
                pass

    removed = before - len(df)
    print(f"  Removed      : {removed:,} duplicate/empty rows")
    print(f"  Clean records: {len(df):,}")
    return df


def find_column(df, keywords):
    """Find first column matching any keyword"""
    for col in df.columns:
        for kw in keywords:
            if kw in col.lower():
                return col
    return None


def safe_stat(series, func):
    """Safely compute a statistic, returns None on failure"""
    try:
        clean = pd.to_numeric(series, errors='coerce').dropna()
        if len(clean) == 0:
            return None
        return func(clean)
    except Exception:
        return None


def analyze_data(df):
    """Generate full analysis report"""
    print("\n" + "="*60)
    print("STEP 3: ANALYZING DATA")
    print("="*60)

    lines = []
    lines.append("="*60)
    lines.append("REAL ESTATE MARKET ANALYSIS REPORT")
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("="*60)

    # Overview
    lines.append(f"\nTotal Properties : {len(df):,}")
    lines.append(f"Total Cities     : {df['City'].nunique()}")
    lines.append(f"Columns          : {list(df.columns)}")

    # City counts
    lines.append("\n" + "-"*40)
    lines.append("PROPERTIES BY CITY")
    lines.append("-"*40)
    for city, count in df['City'].value_counts().items():
        lines.append(f"  {city:12} : {count:>6,}")

    # Price analysis
    price_col = find_column(df, ['price'])
    if price_col:
        lines.append("\n" + "-"*40)
        lines.append(f"PRICE ANALYSIS ({price_col})")
        lines.append("-"*40)
        avg = safe_stat(df[price_col], lambda s: s.mean())
        med = safe_stat(df[price_col], lambda s: s.median())
        mn  = safe_stat(df[price_col], lambda s: s.min())
        mx  = safe_stat(df[price_col], lambda s: s.max())
        if avg is not None: lines.append(f"  Average : {avg:>12,.0f}")
        if med is not None: lines.append(f"  Median  : {med:>12,.0f}")
        if mn  is not None: lines.append(f"  Minimum : {mn:>12,.0f}")
        if mx  is not None: lines.append(f"  Maximum : {mx:>12,.0f}")

        lines.append("\n  Average Price by City:")
        try:
            df_num = df.copy()
            df_num[price_col] = pd.to_numeric(df_num[price_col], errors='coerce')
            city_avg = df_num.groupby('City')[price_col].mean().dropna().sort_values(ascending=False)
            for city, avg in city_avg.items():
                lines.append(f"    {city:12} : {avg:>12,.0f}")
        except Exception as e:
            lines.append(f"    Could not compute: {e}")

    # Area analysis
    area_col = find_column(df, ['area', 'sqft'])
    if area_col and area_col != price_col:
        lines.append("\n" + "-"*40)
        lines.append(f"AREA ANALYSIS ({area_col})")
        lines.append("-"*40)
        avg = safe_stat(df[area_col], lambda s: s.mean())
        mn  = safe_stat(df[area_col], lambda s: s.min())
        mx  = safe_stat(df[area_col], lambda s: s.max())
        if avg is not None: lines.append(f"  Average : {avg:>10,.0f} sqft")
        if mn  is not None: lines.append(f"  Minimum : {mn:>10,.0f} sqft")
        if mx  is not None: lines.append(f"  Maximum : {mx:>10,.0f} sqft")

    # BHK analysis
    bhk_col = find_column(df, ['bhk', 'bedroom'])
    if bhk_col:
        lines.append("\n" + "-"*40)
        lines.append(f"BHK DISTRIBUTION ({bhk_col})")
        lines.append("-"*40)
        try:
            bhk_series = pd.to_numeric(df[bhk_col], errors='coerce').dropna().astype(int)
            if len(bhk_series) > 0:
                for bhk, count in bhk_series.value_counts().head(8).sort_index().items():
                    lines.append(f"  {bhk} BHK : {count:>6,}")
            else:
                for bhk, count in df[bhk_col].value_counts().head(8).items():
                    lines.append(f"  {str(bhk):10} : {count:>6,}")
        except Exception:
            pass

    # City summary table
    summary = pd.DataFrame({'Properties': df['City'].value_counts()})
    if price_col:
        try:
            df_num = df.copy()
            df_num[price_col] = pd.to_numeric(df_num[price_col], errors='coerce')
            summary['Avg_Price'] = df_num.groupby('City')[price_col].mean().round(0)
            summary['Min_Price'] = df_num.groupby('City')[price_col].min()
            summary['Max_Price'] = df_num.groupby('City')[price_col].max()
        except Exception:
            pass
    if area_col and area_col != price_col:
        try:
            df_num = df.copy()
            df_num[area_col] = pd.to_numeric(df_num[area_col], errors='coerce')
            summary['Avg_Area_sqft'] = df_num.groupby('City')[area_col].mean().round(0)
        except Exception:
            pass

    lines.append("\n" + "-"*40)
    lines.append("CITY SUMMARY TABLE")
    lines.append("-"*40)
    lines.append(summary.to_string())

    lines.append("\n" + "="*60)
    lines.append("END OF REPORT")
    lines.append("="*60)

    report = "\n".join(lines)
    print(report)
    return df, summary, report


def save_everything(df, summary, report):
    """Save all outputs to the output folder"""
    print("\n" + "="*60)
    print("STEP 4: SAVING OUTPUTS")
    print("="*60)

    master_path = os.path.join(OUTPUT_FOLDER, MASTER_FILE)
    df.to_csv(master_path, index=False, encoding='utf-8-sig')
    print(f"  [SAVED] Master data   : {master_path}")

    summary_path = os.path.join(OUTPUT_FOLDER, SUMMARY_FILE)
    summary.to_csv(summary_path, encoding='utf-8-sig')
    print(f"  [SAVED] City summary  : {summary_path}")

    report_path = os.path.join(OUTPUT_FOLDER, REPORT_FILE)
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"  [SAVED] Analysis text : {report_path}")

    print("\n  All files saved in the 'output' folder.")


def show_sample(df):
    """Show preview of final data"""
    print("\n" + "="*60)
    print("STEP 5: DATA PREVIEW")
    print("="*60)
    print(df.head(5).to_string())


# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    print("\n" + "="*60)
    print(" REAL ESTATE DATA ANALYZER - FINAL PERFECT VERSION ")
    print("="*60)

    setup()

    df = load_all_cities()
    if df is None:
        exit()

    df = clean_data(df)
    df, summary, report = analyze_data(df)
    save_everything(df, summary, report)
    show_sample(df)

    print("\n" + "="*60)
    print(" PROJECT COMPLETE! ")
    print("="*60)
    print(f" All outputs are in the '{OUTPUT_FOLDER}' folder.")
    print(" Take screenshots and build your portfolio!")
    print("="*60 + "\n")