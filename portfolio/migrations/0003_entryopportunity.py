# Generated migration for EntryOpportunity model

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('portfolio', '0001_initial'),
        ('news', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='EntryOpportunity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('opportunity_type', models.CharField(choices=[('PRICE_DIP', 'Price Dip'), ('ORDER_WIN', 'New Order'), ('DIVIDEND', 'Dividend Announcement'), ('EXPANSION', 'Expansion/Acquisition'), ('SPLIT', 'Stock Split'), ('BONUS', 'Bonus Issue')], max_length=20)),
                ('signal_date', models.DateField()),
                ('signal_strength', models.CharField(choices=[('STRONG', 'Strong'), ('MODERATE', 'Moderate'), ('WEAK', 'Weak')], default='MODERATE', max_length=10)),
                ('price_at_signal', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('percentage_change', models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True)),
                ('description', models.TextField()),
                ('is_active', models.BooleanField(default=True)),
                ('expires_at', models.DateField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('stock', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='entry_opportunities', to='news.stock')),
            ],
            options={
                'verbose_name_plural': 'Entry Opportunities',
                'ordering': ['-signal_date', '-signal_strength'],
            },
        ),
    ]
