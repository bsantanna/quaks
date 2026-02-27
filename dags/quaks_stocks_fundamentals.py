from airflow.sdk import DAG, task
from airflow.providers.cncf.kubernetes.secret import Secret
from datetime import datetime

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2025, 1, 1),
    "retries": 0,
}

dag = DAG(
    "quaks_stocks_fundamentals",
    default_args=default_args,
    schedule="0 6 * * 0",
    catchup=False,
)

@task.kubernetes(
    image="bsantanna/java-python-dev",
    namespace="airflow",
    secrets=[Secret('env', None, 'quaks-dags-secrets')],
)
def load_stocks_fundamentals():
    import os
    import time
    import math
    import requests
    import json
    from datetime import datetime

    def safe_float(val):
        if val is None:
            return None
        try:
            f = float(val)
            return None if math.isnan(f) or math.isinf(f) else f
        except (ValueError, TypeError):
            return None

    def safe_int(val):
        f = safe_float(val)
        return int(f) if f is not None else None

    def finnhub_get(path, params=None):
        finnhub_api_key = os.environ.get('FINNHUB_API_KEY')
        if params is None:
            params = {}
        params['token'] = finnhub_api_key
        return requests.get(f"https://finnhub.io/api/v1{path}", params=params).json()

    def find_val(items, concepts):
        if not items:
            return None
        for concept in concepts:
            for item in items:
                c = item.get('concept', '')
                if concept.lower() in c.lower():
                    return safe_float(item.get('value'))
        return None

    def format_bulk_income_statement(ticker, reports, index_suffix):
        index_name = f"quaks_stocks-fundamental-income-statement_{index_suffix}"
        lines = []
        for report in reports:
            fiscal_date = report.get('endDate', '').split(' ')[0].split('T')[0]
            if not fiscal_date:
                continue
            ic = report.get('report', {}).get('ic', [])
            if not ic:
                continue
            id_str = f"{ticker}_{fiscal_date}"
            meta = {"index": {"_index": index_name, "_id": id_str}}
            doc = {
                "key_ticker": ticker,
                "fiscal_date_ending": fiscal_date,
                "reported_currency": "USD",
                "total_revenue": safe_int(find_val(ic, ['Revenues', 'RevenueFromContractWithCustomerExcludingAssessedTax', 'SalesRevenueNet'])),
                "gross_profit": safe_int(find_val(ic, ['GrossProfit'])),
                "cost_of_revenue": safe_int(find_val(ic, ['CostOfRevenue', 'CostOfGoodsAndServicesSold', 'CostOfGoodsSold'])),
                "cost_of_goods_and_services_sold": safe_int(find_val(ic, ['CostOfGoodsAndServicesSold', 'CostOfRevenue'])),
                "operating_income": safe_int(find_val(ic, ['OperatingIncomeLoss', 'OperatingIncome'])),
                "selling_general_and_administrative": safe_int(find_val(ic, ['SellingGeneralAndAdministrativeExpense'])),
                "research_and_development": safe_int(find_val(ic, ['ResearchAndDevelopmentExpense'])),
                "operating_expenses": safe_int(find_val(ic, ['OperatingExpenses', 'CostsAndExpenses'])),
                "investment_income_net": safe_float(find_val(ic, ['InvestmentIncomeNet'])),
                "net_interest_income": safe_int(find_val(ic, ['InterestIncomeExpenseNet', 'NetInterestIncome'])),
                "interest_income": safe_int(find_val(ic, ['InterestIncome', 'InvestmentIncomeInterest'])),
                "interest_expense": safe_int(find_val(ic, ['InterestExpense'])),
                "non_interest_income": safe_float(find_val(ic, ['NoninterestIncome', 'OtherNonoperatingIncomeExpense'])),
                "other_non_operating_income": safe_float(find_val(ic, ['OtherNonoperatingIncomeExpense', 'NonoperatingIncomeExpense'])),
                "depreciation": safe_float(find_val(ic, ['Depreciation', 'DepreciationAmortizationAndAccretion'])),
                "depreciation_and_amortization": safe_int(find_val(ic, ['DepreciationAndAmortization', 'DepreciationAmortizationAndAccretion'])),
                "income_before_tax": safe_int(find_val(ic, ['IncomeLossFromContinuingOperationsBeforeIncomeTaxes', 'IncomeLossBeforeIncomeTax'])),
                "income_tax_expense": safe_int(find_val(ic, ['IncomeTaxExpenseBenefit'])),
                "interest_and_debt_expense": safe_float(find_val(ic, ['InterestExpense', 'InterestAndDebtExpense'])),
                "net_income_from_continuing_operations": safe_int(find_val(ic, ['IncomeLossFromContinuingOperations'])),
                "comprehensive_income_net_of_tax": safe_float(find_val(ic, ['ComprehensiveIncomeNetOfTax'])),
                "ebit": safe_int(find_val(ic, ['OperatingIncomeLoss', 'OperatingIncome'])),
                "ebitda": None,
                "net_income": safe_int(find_val(ic, ['NetIncomeLoss', 'NetIncome', 'ProfitLoss'])),
            }
            lines.append(json.dumps(meta))
            lines.append(json.dumps(doc))
        return (("\n".join(lines)) + "\n").encode("utf-8") if lines else b""

    def format_bulk_balance_sheet(ticker, reports, index_suffix):
        index_name = f"quaks_stocks-fundamental-balance-sheet_{index_suffix}"
        lines = []
        for report in reports:
            fiscal_date = report.get('endDate', '').split(' ')[0].split('T')[0]
            if not fiscal_date:
                continue
            bs = report.get('report', {}).get('bs', [])
            if not bs:
                continue
            id_str = f"{ticker}_{fiscal_date}"
            meta = {"index": {"_index": index_name, "_id": id_str}}
            doc = {
                "key_ticker": ticker,
                "fiscal_date_ending": fiscal_date,
                "reported_currency": "USD",
                "total_assets": safe_int(find_val(bs, ['Assets'])),
                "total_current_assets": safe_int(find_val(bs, ['AssetsCurrent'])),
                "cash_and_cash_equivalents_at_carrying_value": safe_int(find_val(bs, ['CashAndCashEquivalentsAtCarryingValue', 'CashAndCashEquivalents'])),
                "cash_and_short_term_investments": safe_int(find_val(bs, ['CashCashEquivalentsAndShortTermInvestments'])),
                "inventory": safe_int(find_val(bs, ['InventoryNet', 'Inventory'])),
                "current_net_receivables": safe_int(find_val(bs, ['AccountsReceivableNetCurrent', 'ReceivablesNetCurrent'])),
                "total_non_current_assets": safe_int(find_val(bs, ['AssetsNoncurrent'])),
                "property_plant_equipment": safe_int(find_val(bs, ['PropertyPlantAndEquipmentNet'])),
                "accumulated_depreciation_amortization_ppe": safe_int(find_val(bs, ['AccumulatedDepreciationDepletionAndAmortizationPropertyPlantAndEquipment'])),
                "intangible_assets": safe_int(find_val(bs, ['IntangibleAssetsNetIncludingGoodwill'])),
                "intangible_assets_excluding_goodwill": safe_int(find_val(bs, ['IntangibleAssetsNetExcludingGoodwill', 'FiniteLivedIntangibleAssetsNet'])),
                "goodwill": safe_int(find_val(bs, ['Goodwill'])),
                "investments": safe_int(find_val(bs, ['Investments', 'ShortTermInvestments'])),
                "long_term_investments": safe_int(find_val(bs, ['LongTermInvestments', 'MarketableSecuritiesNoncurrent'])),
                "short_term_investments": safe_int(find_val(bs, ['ShortTermInvestments', 'MarketableSecuritiesCurrent'])),
                "other_current_assets": safe_int(find_val(bs, ['OtherAssetsCurrent'])),
                "other_non_current_assets": safe_int(find_val(bs, ['OtherAssetsNoncurrent'])),
                "total_liabilities": safe_int(find_val(bs, ['Liabilities'])),
                "total_current_liabilities": safe_int(find_val(bs, ['LiabilitiesCurrent'])),
                "current_accounts_payable": safe_int(find_val(bs, ['AccountsPayableCurrent', 'AccountsPayable'])),
                "deferred_revenue": safe_int(find_val(bs, ['DeferredRevenueCurrent', 'DeferredRevenue', 'ContractWithCustomerLiabilityCurrent'])),
                "current_debt": safe_int(find_val(bs, ['DebtCurrent', 'ShortTermBorrowings', 'CommercialPaper'])),
                "short_term_debt": safe_int(find_val(bs, ['ShortTermBorrowings', 'DebtCurrent'])),
                "total_non_current_liabilities": safe_int(find_val(bs, ['LiabilitiesNoncurrent'])),
                "capital_lease_obligations": safe_int(find_val(bs, ['CapitalLeaseObligations', 'OperatingLeaseLiability'])),
                "long_term_debt": safe_int(find_val(bs, ['LongTermDebtNoncurrent', 'LongTermDebt'])),
                "current_long_term_debt": safe_int(find_val(bs, ['LongTermDebtCurrent'])),
                "long_term_debt_noncurrent": safe_int(find_val(bs, ['LongTermDebtNoncurrent', 'LongTermDebt'])),
                "short_long_term_debt_total": safe_int(find_val(bs, ['DebtAndCapitalLeaseObligations'])),
                "other_current_liabilities": safe_int(find_val(bs, ['OtherLiabilitiesCurrent'])),
                "other_non_current_liabilities": safe_int(find_val(bs, ['OtherLiabilitiesNoncurrent'])),
                "total_shareholder_equity": safe_int(find_val(bs, ['StockholdersEquity'])),
                "treasury_stock": safe_int(find_val(bs, ['TreasuryStockValue', 'TreasuryStockShares'])),
                "retained_earnings": safe_int(find_val(bs, ['RetainedEarningsAccumulatedDeficit'])),
                "common_stock": safe_int(find_val(bs, ['CommonStockValue', 'CommonStocksIncludingAdditionalPaidInCapital'])),
                "common_stock_shares_outstanding": safe_int(find_val(bs, ['CommonStockSharesOutstanding'])),
            }
            lines.append(json.dumps(meta))
            lines.append(json.dumps(doc))
        return (("\n".join(lines)) + "\n").encode("utf-8") if lines else b""

    def format_bulk_cash_flow(ticker, reports, index_suffix):
        index_name = f"quaks_stocks-fundamental-cash-flow_{index_suffix}"
        lines = []
        for report in reports:
            fiscal_date = report.get('endDate', '').split(' ')[0].split('T')[0]
            if not fiscal_date:
                continue
            cf = report.get('report', {}).get('cf', [])
            if not cf:
                continue
            id_str = f"{ticker}_{fiscal_date}"
            meta = {"index": {"_index": index_name, "_id": id_str}}
            doc = {
                "key_ticker": ticker,
                "fiscal_date_ending": fiscal_date,
                "reported_currency": "USD",
                "operating_cashflow": safe_int(find_val(cf, ['NetCashProvidedByUsedInOperatingActivities', 'NetCashProvidedByOperatingActivities'])),
                "payments_for_operating_activities": None,
                "proceeds_from_operating_activities": None,
                "change_in_operating_liabilities": safe_int(find_val(cf, ['IncreaseDecreaseInAccountsPayable', 'IncreaseDecreaseInOtherOperatingLiabilities'])),
                "change_in_operating_assets": safe_int(find_val(cf, ['IncreaseDecreaseInOtherOperatingAssets'])),
                "depreciation_depletion_and_amortization": safe_int(find_val(cf, ['DepreciationDepletionAndAmortization', 'DepreciationAndAmortization'])),
                "capital_expenditures": safe_int(find_val(cf, ['PaymentsToAcquirePropertyPlantAndEquipment', 'CapitalExpenditures'])),
                "change_in_receivables": safe_int(find_val(cf, ['IncreaseDecreaseInAccountsReceivable'])),
                "change_in_inventory": safe_int(find_val(cf, ['IncreaseDecreaseInInventories'])),
                "profit_loss": safe_int(find_val(cf, ['NetIncomeLoss', 'ProfitLoss'])),
                "cashflow_from_investment": safe_int(find_val(cf, ['NetCashProvidedByUsedInInvestingActivities'])),
                "cashflow_from_financing": safe_int(find_val(cf, ['NetCashProvidedByUsedInFinancingActivities'])),
                "proceeds_from_repayments_of_short_term_debt": safe_int(find_val(cf, ['ProceedsFromRepaymentsOfShortTermDebt', 'RepaymentsOfShortTermDebt'])),
                "payments_for_repurchase_of_common_stock": safe_int(find_val(cf, ['PaymentsForRepurchaseOfCommonStock'])),
                "payments_for_repurchase_of_equity": safe_int(find_val(cf, ['PaymentsForRepurchaseOfCommonStock', 'PaymentsForRepurchaseOfEquity'])),
                "payments_for_repurchase_of_preferred_stock": safe_int(find_val(cf, ['PaymentsForRepurchaseOfPreferredStockAndPreferenceStock'])),
                "dividend_payout": safe_int(find_val(cf, ['PaymentsOfDividends', 'PaymentsOfDividendsCommonStock'])),
                "dividend_payout_common_stock": safe_int(find_val(cf, ['PaymentsOfDividendsCommonStock', 'PaymentsOfDividends'])),
                "dividend_payout_preferred_stock": safe_int(find_val(cf, ['PaymentsOfDividendsPreferredStockAndPreferenceStock'])),
                "proceeds_from_issuance_of_common_stock": safe_int(find_val(cf, ['ProceedsFromIssuanceOfCommonStock'])),
                "proceeds_from_issuance_of_long_term_debt_and_capital_securities_net": safe_int(find_val(cf, ['ProceedsFromIssuanceOfLongTermDebt'])),
                "proceeds_from_issuance_of_preferred_stock": safe_int(find_val(cf, ['ProceedsFromIssuanceOfPreferredStock'])),
                "proceeds_from_repurchase_of_equity": None,
                "proceeds_from_sale_of_treasury_stock": None,
                "change_in_cash_and_cash_equivalents": safe_int(find_val(cf, ['CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalentsPeriodIncreaseDecreaseIncludingExchangeRateEffect', 'CashAndCashEquivalentsPeriodIncreaseDecrease'])),
                "change_in_exchange_rate": safe_int(find_val(cf, ['EffectOfExchangeRateOnCashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents'])),
                "net_income": safe_int(find_val(cf, ['NetIncomeLoss', 'ProfitLoss'])),
            }
            lines.append(json.dumps(meta))
            lines.append(json.dumps(doc))
        return (("\n".join(lines)) + "\n").encode("utf-8") if lines else b""

    def ingest_fundamentals(ticker, index_suffix="latest"):
        es_url = os.environ.get('ELASTICSEARCH_URL')
        es_api_key = os.environ.get('ELASTICSEARCH_API_KEY')
        headers = {
            'Authorization': f'ApiKey {es_api_key}',
            'Content-Type': 'application/x-ndjson'
        }

        result = finnhub_get('/stock/financials-reported', {
            'symbol': ticker,
            'freq': 'quarterly',
        })
        reports = result.get('data', [])

        if not reports:
            print(f"  No financials-reported data for {ticker}")
            return

        # Income Statement
        data = format_bulk_income_statement(ticker, reports, index_suffix)
        if data:
            resp = requests.post(url=f"{es_url}/_bulk", headers=headers, data=data)
            print(f"  Income statement for {ticker}: {resp.status_code}")

        # Balance Sheet
        data = format_bulk_balance_sheet(ticker, reports, index_suffix)
        if data:
            resp = requests.post(url=f"{es_url}/_bulk", headers=headers, data=data)
            print(f"  Balance sheet for {ticker}: {resp.status_code}")

        # Cash Flow
        data = format_bulk_cash_flow(ticker, reports, index_suffix)
        if data:
            resp = requests.post(url=f"{es_url}/_bulk", headers=headers, data=data)
            print(f"  Cash flow for {ticker}: {resp.status_code}")

    api_endpoint = "https://quaks.ai"
    indexed_key_ticker_list = requests.get(f"{api_endpoint}/json/indexed_key_ticker_list.json").json()

    for company in indexed_key_ticker_list:
        ticker = company["key_ticker"]
        index = company["index"]
        try:
            print(f"Processing fundamentals for {ticker}...")
            ingest_fundamentals(ticker, index)
        except Exception as e:
            print(f"Error processing fundamentals for {ticker}: {e}")
        time.sleep(1)

with dag:
    load_stocks_fundamentals()
