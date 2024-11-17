from django import forms
from MyPay.models import Guest
from PekerjaanJasa.models import Job

class TransactionForm(forms.Form):
    TOPUP = 'topup'
    PAY_JOB = 'pay_job'
    TRANSFER = 'transfer'
    WITHDRAWAL = 'withdrawal'

    TRANSACTION_CATEGORIES = [
        (TOPUP, 'TopUp MyPay'),
        (PAY_JOB, 'Bayar Jasa'),
        (TRANSFER, 'Transfer MyPay'),
        (WITHDRAWAL, 'Withdrawal'),
    ]
    
    transaction_category = forms.ChoiceField(choices=TRANSACTION_CATEGORIES, label="Kategori Transaksi")
    
    # State 1: TopUp MyPay
    topup_amount = forms.DecimalField(label="Nominal TopUp", max_digits=10, decimal_places=2, required=False)

    # State 2: Pay Job (for users only)
    job_order = forms.ModelChoiceField(queryset=Job.objects.all(), required=False, label="Jasa yang dipesan")
    price = forms.DecimalField(max_digits=10, decimal_places=2, required=False, label="Harga Pemesanan")

    # State 3: Transfer MyPay
    transfer_phone = forms.CharField(max_length=15, required=False, label="No HP Tujuan")
    transfer_amount = forms.DecimalField(max_digits=10, decimal_places=2, required=False, label="Nominal Transfer")
    
    # State 4: Withdrawal
    bank_name = forms.CharField(max_length=100, required=False, label="Nama Bank")
    account_number = forms.CharField(max_length=20, required=False, label="Nomor Rekening")
    withdrawal_amount = forms.DecimalField(max_digits=10, decimal_places=2, required=False, label="Nominal Withdrawal")
