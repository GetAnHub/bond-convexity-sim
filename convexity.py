import pandas as pd
import numpy as np
from datetime import datetime
from scipy.optimize import newton
import matplotlib.pyplot as plt

# Existing functions (unchanged)
def convert_date(date_str):
    if pd.isna(date_str) or not isinstance(date_str, str):
        return date_str
    try:
        date_str = ' '.join(date_str.split()).strip()
        month_map = {
            'Jan': '1', 'Feb': '2', 'Mar': '3', 'Apr': '4', 'May': '5', 'Jun': '6',
            'Jul': '7', 'Aug': '8', 'Sep': '9', 'Oct': '10', 'Nov': '11', 'Dec': '12'
        }
        month = date_str[:3]
        month_num = month_map.get(month)
        if not month_num:
            print(f"Mese non riconosciuto: {date_str}")
            return date_str
        date_clean = date_str.replace(month + ' ', month_num + '/').replace(', ', '/')
        date_obj = datetime.strptime(date_clean, '%m/%d/%Y')
        return date_obj.strftime('%d/%m/%Y')
    except Exception as e:
        print(f"Errore nella conversione di '{date_str}': {e}")
        return date_str

def bond_price(par_value, coupon_rate, periods, ytm, coupon_frequency=2):
    if pd.isna(par_value) or pd.isna(coupon_rate) or pd.isna(periods) or pd.isna(ytm) or periods <= 0:
        print(f"Input non validi per bond_price: par_value={par_value}, coupon_rate={coupon_rate}, periods={periods}, ytm={ytm}")
        return np.nan
    try:
        par_value = float(par_value)
        coupon_rate = float(coupon_rate)
        ytm = float(ytm)
        coupon = (coupon_rate / 100) * par_value / coupon_frequency
        discount_factor = 1 / (1 + ytm / coupon_frequency)
        coupon_pv = coupon * (1 - discount_factor ** periods) / (ytm / coupon_frequency)
        par_pv = par_value * discount_factor ** periods
        return coupon_pv + par_pv
    except (ValueError, TypeError) as e:
        print(f"Errore in bond_price: par_value={par_value}, coupon_rate={coupon_rate}, periods={periods}, ytm={ytm}, errore={e}")
        return np.nan

def calculate_ytm(price, par_value, coupon_rate, periods, coupon_frequency=2):
    if pd.isna(price) or pd.isna(par_value) or pd.isna(coupon_rate) or pd.isna(periods) or periods <= 0:
        print(f"Input non validi per calculate_ytm: price={price}, par_value={par_value}, coupon_rate={coupon_rate}, periods={periods}")
        return np.nan
    try:
        price = float(price)
        par_value = float(par_value)
        coupon_rate = float(coupon_rate)
        def bond_price_error(ytm_guess):
            return bond_price(par_value, coupon_rate, periods, ytm_guess, coupon_frequency) - price
        ytm = newton(bond_price_error, 0.05, maxiter=150)
        return ytm * 100
    except (ValueError, TypeError, RuntimeError) as e:
        print(f"Errore in calculate_ytm: price={price}, par_value={par_value}, coupon_rate={coupon_rate}, periods={periods}, errore={e}")
        return np.nan

def calculate_accrued_interest(par_value, coupon_rate, issue_date, purchase_date, coupon_frequency=1):
    """
    Calculate accrued interest from the last coupon date to the purchase date.
    
    Parameters:
    - par_value: Face value of the bond (float)
    - coupon_rate: Annual coupon rate in percentage (float)
    - issue_date: Issue date in format 'DD/MM/YYYY' (str)
    - purchase_date: Purchase date in format 'DD/MM/YYYY' (str)
    - coupon_frequency: Number of coupon payments per year (int, default=1)
    
    Returns:
    - Accrued interest (float), or np.nan if calculation fails
    """
    try:
        par_value = float(par_value)
        coupon_rate = float(coupon_rate)
        issue = datetime.strptime(issue_date, '%d/%m/%Y')
        purchase = datetime.strptime(purchase_date, '%d/%m/%Y')
        
        # Assume coupons are paid on issue date anniversary
        coupon_interval = 365.25 / coupon_frequency  # Days between coupons
        years_since_issue = (purchase - issue).days / 365.25
        coupons_paid = int(years_since_issue * coupon_frequency)
        last_coupon_date = issue
        for _ in range(coupons_paid):
            last_coupon_date = last_coupon_date.replace(year=last_coupon_date.year + 1 if coupon_frequency == 1 else last_coupon_date.year)
        
        days_since_last_coupon = (purchase - last_coupon_date).days
        if days_since_last_coupon < 0:
            days_since_last_coupon += coupon_interval
            last_coupon_date = last_coupon_date.replace(year=last_coupon_date.year - 1)
        
        annual_coupon = (coupon_rate / 100) * par_value
        accrued_interest = annual_coupon * (days_since_last_coupon / coupon_interval)
        return accrued_interest
    except Exception as e:
        print(f"Errore in calculate_accrued_interest: {e}")
        return np.nan

def calculate_modified_duration(par_value, coupon_rate, periods, ytm, coupon_frequency=1):
    """
    Calculate modified duration of the bond.
    
    Parameters:
    - par_value: Face value of the bond (float)
    - coupon_rate: Annual coupon rate in percentage (float)
    - periods: Number of coupon periods until maturity (int)
    - ytm: Yield to maturity (float, in decimal form, e.g., 0.05 for 5%)
    - coupon_frequency: Number of coupon payments per year (int, default=1)
    
    Returns:
    - Modified duration (float), or np.nan if calculation fails
    """
    try:
        par_value = float(par_value)
        coupon_rate = float(coupon_rate)
        ytm = float(ytm)
        coupon = (coupon_rate / 100) * par_value / coupon_frequency
        discount_rate = ytm / coupon_frequency
        macaulay_duration = 0
        present_value_total = 0
        
        # Calculate Macaulay duration
        for t in range(1, int(periods) + 1):
            cash_flow = coupon if t < periods else coupon + par_value
            pv_cash_flow = cash_flow / (1 + discount_rate) ** t
            macaulay_duration += t * pv_cash_flow
            present_value_total += pv_cash_flow
        
        if present_value_total == 0:
            print(f"Errore: prezzo presente totale è zero")
            return np.nan
        
        macaulay_duration /= present_value_total
        modified_duration = macaulay_duration / (1 + discount_rate)
        return modified_duration
    except (ValueError, TypeError) as e:
        print(f"Errore in calculate_modified_duration: {e}")
        return np.nan

def calculate_ytm_range(par_value, coupon_rate, periods, coupon_frequency, min_price, max_price, num_points=100):
    """
    Calculate YTM for a range of bond prices.
    
    Parameters:
    - par_value: Face value of the bond (float)
    - coupon_rate: Annual coupon rate in percentage (float)
    - periods: Number of coupon periods until maturity (int)
    - coupon_frequency: Number of coupon payments per year (int)
    - min_price: Minimum price for the range (float)
    - max_price: Maximum price for the range (float)
    - num_points: Number of price points to evaluate (int, default=100)
    
    Returns:
    - Tuple of (prices, ytms) arrays
    """
    try:
        prices = np.linspace(min_price, max_price, num_points)
        ytms = []
        for price in prices:
            ytm = calculate_ytm(price, par_value, coupon_rate, periods, coupon_frequency)
            ytms.append(ytm if not pd.isna(ytm) else np.nan)
        return prices, np.array(ytms)
    except Exception as e:
        print(f"Errore in calculate_ytm_range: {e}")
        return None, None

def plot_price_yield_curve(par_value, coupon_rate, periods, coupon_frequency, min_price, max_price, num_points=100):
    """
    Plot the price-yield curve for a bond with price on y-axis and YTM on x-axis.
    
    Parameters:
    - par_value: Face value of the bond (float)
    - coupon_rate: Annual coupon rate in percentage (float)
    - periods: Number of coupon periods until maturity (int)
    - coupon_frequency: Number of coupon payments per year (int)
    - min_price: Minimum price for the plot (float)
    - max_price: Maximum price for the plot (float)
    - num_points: Number of price points to evaluate (int, default=100)
    
    Returns:
    - None (displays the plot)
    """
    try:
        prices, ytms = calculate_ytm_range(par_value, coupon_rate, periods, coupon_frequency, min_price, max_price, num_points)
        if prices is None or ytms is None:
            print("Impossibile generare il grafico a causa di un errore nei dati")
            return
        
        plt.figure(figsize=(10, 6))
        plt.plot(ytms, prices, label='Price-Yield Curve', color='blue')
        plt.xlabel('Yield to Maturity (%)')
        plt.ylabel('Bond Price')
        plt.title('Price-Yield Curve for Bond')
        plt.grid(True)
        plt.legend()
        plt.show()
    except Exception as e:
        print(f"Errore in plot_price_yield_curve: {e}")

def calculate_ytm_from_bond_data(price, par_value, coupon_rate, maturity_date, purchase_date, coupon_frequency=1, issue_price=None, min_price=None, max_price=None):
    """
    Calculate YTM, accrued interest, and modified duration given bond data, with optional price-yield plot.
    
    Parameters:
    - price: Clean market price of the bond (float)
    - par_value: Face value of the bond (float)
    - coupon_rate: Annual coupon rate in percentage (float)
    - maturity_date: Maturity date in format 'DD/MM/YYYY' (str)
    - purchase_date: Purchase date in format 'DD/MM/YYYY' (str)
    - coupon_frequency: Number of coupon payments per year (int, default=1)
    - issue_price: Issue price of the bond (float, optional, for reference only)
    - min_price: Minimum price for price-yield plot (float, optional)
    - max_price: Maximum price for price-yield plot (float, optional)
    
    Returns:
    - Dictionary with YTM (%), accrued interest, and modified duration, or None if calculation fails
    """
    try:
        # Calculate periods from purchase date to maturity
        purchase = datetime.strptime(purchase_date, '%d/%m/%Y')
        maturity = datetime.strptime(maturity_date, '%d/%m/%Y')
        if maturity <= purchase:
            print(f"Data di maturità ({maturity_date}) non successiva alla data di acquisto")
            return None
        delta = maturity - purchase
        periods = round(delta.days / 365.25 * coupon_frequency)
        if periods <= 0:
            print(f"Periodi calcolati come zero o negativi per: {maturity_date}")
            return None
        
        # Calculate accrued interest
        accrued_interest = calculate_accrued_interest(par_value, coupon_rate, "20/09/2017", purchase_date, coupon_frequency)
        if pd.isna(accrued_interest):
            return None
        
        # Calculate dirty price (clean price + accrued interest)
        dirty_price = price + accrued_interest
        
        # Calculate YTM using dirty price
        ytm = calculate_ytm(dirty_price, par_value, coupon_rate, periods, coupon_frequency)
        if pd.isna(ytm):
            return None
        
        # Calculate modified duration
        modified_duration = calculate_modified_duration(par_value, coupon_rate, periods, ytm / 100, coupon_frequency)
        if pd.isna(modified_duration):
            return None
        
        # Plot price-yield curve if min_price and max_price are provided
        if min_price is not None and max_price is not None:
            plot_price_yield_curve(par_value, coupon_rate, periods, coupon_frequency, min_price, max_price)
        
        # Log issue price for reference (not used in calculation)
        if issue_price is not None:
            print(f"Prezzo di emissione (per riferimento): {issue_price}")
        
        return {
            "ytm": ytm,
            "accrued_interest": accrued_interest,
            "modified_duration": modified_duration
        }
    except Exception as e:
        print(f"Errore in calculate_ytm_from_bond_data: {e}")
        return None

# Example usage for the bond
if __name__ == "__main__":
    price = 48
    par_value = 100.00
    coupon_rate = 2.10
    maturity_date = "20/09/2117"
    purchase_date = "25/12/2025"
    coupon_frequency = 1
    issue_price = 99.502
    min_price = 30  # Example range for plotting
    max_price = 180
    
    result = calculate_ytm_from_bond_data(price, par_value, coupon_rate, maturity_date, purchase_date, coupon_frequency, issue_price, min_price, max_price)
    if result:
        print(f"Yield to Maturity: {result['ytm']:.4f}%")
        print(f"Accrued Interest: {result['accrued_interest']:.4f}")
        print(f"Modified Duration: {result['modified_duration']:.4f} years")
