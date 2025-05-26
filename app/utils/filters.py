from datetime import datetime

def datetime_format(value, format='%d-%m-%Y'):
    """Format datetime untuk template"""
    if value is None:
        return ""
    if isinstance(value, str):
        try:
            value = datetime.strptime(value, '%Y-%m-%d')
        except ValueError:
            return value
    return value.strftime(format)

def currency_format(value):
    """Format angka sebagai currency"""
    if value is None:
        return "Rp 0"
    return f"Rp {value:,.0f}"

def percentage_format(value):
    """Format angka sebagai persentase"""
    if value is None:
        return "0%"
    return f"{value:.1f}%"