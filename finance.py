import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def calculate_income_tax(income):
    # Federal tax rates and thresholds
    federal_rates = [(0.15, 55867), (0.205, 111733), (0.26, 173205), (0.29, 246752)]
    federal_excess_rate = 0.33
    federal_exemption = 15705

    # Ontario tax rates and thresholds
    ontario_rates = [(0.0505, 51446), (0.0915, 102894), (0.1116, 150000), (0.1216, 220000)]
    ontario_excess_rate = 0.1316
    ontario_exemption = 12399

    def calculate_tax(rates, excess_rate, income):
        tax = 0
        prev_threshold = 0
        for rate, threshold in rates:
            if income > threshold:
                tax += (threshold - prev_threshold) * rate
            else:
                tax += (income - prev_threshold) * rate
                return tax
            prev_threshold = threshold
        tax += (income - prev_threshold) * excess_rate
        return tax

    federal_tax = calculate_tax(federal_rates, federal_excess_rate, income - federal_exemption)
    ontario_tax = calculate_tax(ontario_rates, ontario_excess_rate, income - ontario_exemption)

    total_tax = federal_tax + ontario_tax
    return total_tax

def calculate_tax_return_from_rrsp(income, rrsp_contribution):
    # Calculate the initial tax without RRSP contributions
    initial_tax = calculate_income_tax(income)

    # Calculate the new taxable income with the RRSP contribution
    new_taxable_income = income - rrsp_contribution

    # Ensure that the new taxable income does not go below zero
    new_taxable_income = max(new_taxable_income, 0)

    # Calculate the new tax with the reduced taxable income
    new_tax = calculate_income_tax(new_taxable_income)

    # The tax return is the difference in tax due to the RRSP contribution
    tax_return = initial_tax - new_tax
    return tax_return

def calculate_rolling_contribution_returns(initial_investment, monthly_contribution, annual_interest_rate, investment_period_months):
    """
    Calculate the future value of a rolling set of monthly contributions.

    :param initial_investment: Initial amount invested.
    :param monthly_contribution: Amount contributed every month.
    :param annual_interest_rate: Annual interest rate in percentage.
    :param investment_period_months: Total investment period in months.
    :return: The future value of the investment.
    """
    monthly_interest_rate = annual_interest_rate / 12 / 100
    future_value = [initial_investment]

    for idx in range(1, investment_period_months + 1):
        # Apply interest to the current amount
        value = future_value[-1]
        value *= (1 + monthly_interest_rate)
        value += monthly_contribution  # Add the monthly contribution for the next period
        future_value.append(value)
        # future_value *= (1 + monthly_interest_rate)
        
        # future_value += monthly_contribution

    return future_value[1:]

def calculate_remaining_mortgage(principal, annual_interest_rate, amortization_period_months, payments_made):
    """
    Calculate the remaining mortgage amount.

    :param principal: The initial amount of the loan.
    :param annual_interest_rate: The annual interest rate as a percentage.
    :param amortization_period_months: The total number of payments for the loan (amortization period in months).
    :param payments_made: The number of payments made so far.
    :return: The remaining mortgage amount.
    """
    monthly_interest_rate = annual_interest_rate / 12 / 100

    # Monthly mortgage payment using the formula for an amortizing loan
    monthly_payment = principal * (monthly_interest_rate * (1 + monthly_interest_rate) ** amortization_period_months) / ((1 + monthly_interest_rate) ** amortization_period_months - 1)

    # Remaining balance formula
    remaining_balance = (monthly_payment / monthly_interest_rate) * (1 - (1 + monthly_interest_rate) ** (- (amortization_period_months - payments_made)))

    return remaining_balance

# Set page config
st.set_page_config(page_title='Real Estate Investment Analysis', layout='wide')

# Title of the dashboard
st.title('Real Estate Investment Analysis Dashboard')

# Economic Predictors
st.sidebar.header('Economic Parameters')
price_appreciation = st.sidebar.number_input('Home Appreciation (%)', value=0.00)
price_depreciation = st.sidebar.number_input('Home Depreciation (%)', value=0.00)
timeline = st.sidebar.number_input('Forecasting Horizon (years)', value=5)
# inflation = st.sidebar.number_input('Inflation (%)')

# Sidebar inputs for financial values
st.sidebar.header('Input Variables - Home')
mortgage_principal = st.sidebar.number_input('Mortgage Principal ($)', value=100000.0)
mortgage_interest_rate = st.sidebar.number_input('Mortgage Interest Rate (%)', value=3.0)
sell_price = st.sidebar.number_input('Sell Price ($)', value=200000.0)
purchase_price = st.sidebar.number_input('Purchase Price ($)', value=150000.0)
realtor_fee = st.sidebar.number_input('Realtor Fee (%)', value=5.0)


# Sidebar inputs for capital growth
st.sidebar.header('Capital Growth')
monthly_rental_income = st.sidebar.number_input("Monthly Rental Income ($)", value=2000.0)
net_starting_capital = st.sidebar.number_input("Starting capital", value=50000.0)
gic_rate = st.sidebar.number_input('GIC Rate (%)', value=2.0)
rrsp_contributions = st.sidebar.number_input('RRSP Contributions ($)', value=5000.0)
annual_income = st.sidebar.number_input('Annual Income ($)', value=100000.0)
first_time_buyer_discount = 5000


# Calculating the values for the time series based on inputs
# Here you can include your specific financial model
# For demonstration, I'm calculating monthly mortgage payments and investment growth
monthly_interest_rate = mortgage_interest_rate / 100 / 12
num_payments = 22 * 12  # Assuming a 22 year mortgage
monthly_payment = mortgage_principal * (monthly_interest_rate * (1 + monthly_interest_rate) ** num_payments) / ((1 + monthly_interest_rate) ** num_payments - 1)

rrsp = rrsp_contributions * ((1 + gic_rate / 100) ** (num_payments / 12))  # Simple compound interest

# Creating time series for mortgage payments and investment over time
months = np.arange(1, timeline * 12 + 1)
# mortgage_balance = mortgage_principal - mortgage_principal * ((1 + monthly_interest_rate) ** months - 1) / (monthly_interest_rate * (1 + monthly_interest_rate) ** months)
mortgage_balance = calculate_remaining_mortgage(mortgage_principal, mortgage_interest_rate, amortization_period_months=22*12, payments_made=months)

# Capital Growth - Sell
net_capital = net_starting_capital + (sell_price * (1 - realtor_fee / 100) - mortgage_principal)
init_capital_growth = (net_capital * (1 + gic_rate / 100) ** (months / 12))  # GIC Growth
investment_value = init_capital_growth + rrsp_contributions + (rrsp_contributions * (1 + gic_rate / 100) ** (months / 12))  # RRSP Growth

# Capital Growth - Keep
rent_contributions = calculate_rolling_contribution_returns(monthly_rental_income, monthly_contribution=monthly_rental_income, annual_interest_rate=gic_rate, investment_period_months=timeline * 12)
init_capital_growth = net_starting_capital + (net_starting_capital * (1 + gic_rate / 100) ** (months / 12))  # GIC Growth
yearly_tax_return = calculate_tax_return_from_rrsp(annual_income, monthly_rental_income * 12)
sequence_tax_return = [yearly_tax_return if i % 12 == 0 else 0 for i in months]
total_capital = rent_contributions + init_capital_growth + sequence_tax_return
final_sale_price = sell_price * (1 + price_appreciation / 100)**(timeline) / ((1 - price_depreciation / 100)**(timeline))

# Plotting
fig, ax = plt.subplots()
ax.plot(months, mortgage_balance, label='Mortgage Balance')
ax.plot(months, investment_value, label='Investment Growth - Sell')
ax.plot(months, total_capital, label='Investment Growth - Keep')
plt.title('Mortgage and Investment Over Time')
plt.xlabel('Months')
plt.ylabel('Value ($)')
plt.legend()
st.pyplot(fig)

# Displaying calculated results
st.header('Summary of Financial Analysis')
st.write(f'Monthly Mortgage Payment: ${monthly_payment:.2f}')
st.write(f'Total Investment Value after {timeline} years: ${investment_value[-1]:.2f}')
st.write(f'Net Gain/Loss from Selling Immediately: ${(sell_price * (1 - realtor_fee / 100) - purchase_price) - first_time_buyer_discount:.2f}')
st.write(f'Net Gain/Loss from Selling At End of Timeline: ${final_sale_price - purchase_price - first_time_buyer_discount:.2f}')
st.write(f"Capital Upon Selling At End of Timeline: {total_capital[-1]:2f}")
st.write("""
         All figures assume that any invested funds will be invested in a GIC & that the full tax return from rental income contributions goes towards a GIC
         on a rolling basis. RRSP contributions are otherwise considered one time at the start of the period. This does not consider capital growth of outside
         RRSP contributions. This does not consider taxation on income from taxable accounts. An ammortization period of 22 years is assumed.
         """)