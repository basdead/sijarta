# Generated by Django 4.2.4 on 2024-11-07 15:03

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('MyPay', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='MyPayTransaction',
            fields=[
                ('id_transaksi', models.CharField(max_length=10, primary_key=True, serialize=False)),
                ('transaction_type', models.CharField(choices=[('top_up', 'Top Up'), ('payment', 'Pembayaran Jasa'), ('transfer', 'Transfer'), ('withdrawal', 'Penarikan')], max_length=20)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('destination_phone', models.CharField(blank=True, max_length=15, null=True)),
                ('bank_account', models.CharField(blank=True, max_length=30, null=True)),
                ('date', models.DateTimeField(auto_now_add=True)),
                ('guest', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='MyPay.guest')),
            ],
        ),
    ]
