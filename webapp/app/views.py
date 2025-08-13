from datetime import datetime, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import models
from django.db.models import Sum
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.http import require_GET

from .models import Customer, Invoice


def home(request):
    if not request.user.is_authenticated:
        return render(request, 'app/not_loggedin.html')
    return render(request, 'app/index.html')

@login_required
@require_GET
def search_customers(request):
    q = request.GET.get('q', '').strip()
    field = request.GET.get('field', 'any')
    print(f"Search by: {field}, Query: {q}")
    results = []
    if q:
        if field == 'name':
            customers = Customer.objects.filter(name__icontains=q)
        elif field == 'phone':
            customers = Customer.objects.filter(phone_number__icontains=q)
        else:  # 'any'
            customers = Customer.objects.filter(
                models.Q(name__icontains=q) | models.Q(phone_number__icontains=q)
            )
    else:
        customers = Customer.objects.all()

    # Annotate with last purchase date and order by it descending
    customers = customers.annotate(
        last_purchase=models.Max('invoices__date')
    ).order_by('-last_purchase')[:10]

    results = [
        {'cid': c.cid, 'name': c.name, 'phone_number': c.phone_number}
        for c in customers
    ]
    return JsonResponse({'results': results})

@login_required
@require_GET
def search_invoices(request):
    q = request.GET.get('q', '').strip()
    field = request.GET.get('field', 'any')
    date_from = request.GET.get('date_from', '').strip()
    date_to = request.GET.get('date_to', '').strip()
    amount_min = request.GET.get('amount_min', '').strip()
    amount_max = request.GET.get('amount_max', '').strip()
    loyalty_status = request.GET.get('loyalty_status', '').strip()
    referral_status = request.GET.get('referral_status', '').strip()
    has_referrer = request.GET.get('has_referrer', '').strip()

    print(f"Invoice search - Field: {field}, Query: {q}, Date: {date_from}-{date_to}")

    # Start with all invoices
    invoices = Invoice.objects.all()

    # Apply text search filters
    if q:
        if field == 'iid':
            invoices = invoices.filter(iid__icontains=q)
        elif field == 'customer':
            invoices = invoices.filter(customer__name__icontains=q)
        elif field == 'phone':
            invoices = invoices.filter(customer__phone_number__icontains=q)
        elif field == 'referrer':
            invoices = invoices.filter(referrer__name__icontains=q)
        else:  # 'any'
            invoices = invoices.filter(
                models.Q(iid__icontains=q) |
                models.Q(customer__name__icontains=q) |
                models.Q(customer__phone_number__icontains=q) |
                models.Q(referrer__name__icontains=q)
            )

    # Apply date filters
    if date_from:
        try:
            from_date = datetime.strptime(date_from, '%Y-%m-%d').date()
            invoices = invoices.filter(date__gte=from_date)
        except ValueError:
            pass

    if date_to:
        try:
            to_date = datetime.strptime(date_to, '%Y-%m-%d').date()
            invoices = invoices.filter(date__lte=to_date)
        except ValueError:
            pass

    # Apply amount filters
    if amount_min:
        try:
            min_amount = float(amount_min)
            invoices = invoices.filter(total_amount__gte=min_amount)
        except ValueError:
            pass

    if amount_max:
        try:
            max_amount = float(amount_max)
            invoices = invoices.filter(total_amount__lte=max_amount)
        except ValueError:
            pass

    # Apply status filters
    if loyalty_status:
        invoices = invoices.filter(loyalty_points_status=loyalty_status)

    if referral_status:
        invoices = invoices.filter(referral_points_status=referral_status)

    # Apply referrer filter
    if has_referrer == 'yes':
        invoices = invoices.filter(referrer__isnull=False)
    elif has_referrer == 'no':
        invoices = invoices.filter(referrer__isnull=True)

    # Order by date descending and limit results
    invoices = invoices.select_related('customer', 'referrer').order_by('-date')[:20]

    results = [
        {
            'iid': inv.iid,
            'customer_name': inv.customer.name,
            'customer_phone': inv.customer.phone_number,
            'date': inv.date.isoformat(),
            'total_amount': str(inv.total_amount),
            'referrer_name': inv.referrer.name if inv.referrer else None,
            'loyalty_points_status': inv.loyalty_points_status,
            'referral_points_status': inv.referral_points_status,
        }
        for inv in invoices
    ]

    return JsonResponse({'results': results})

def customer_detail(request, cid):
    if not request.user.is_authenticated:
        return render(request, 'app/not_loggedin.html')

    customer = Customer.objects.get(cid=cid)
    
    # run a for loop over all the invoices of this customer... and just save it... this will recalculate their status
    for invoice in customer.invoices.all():
        invoice.save()

    # Calculate total loyalty points (active only)
    loyalty_points = customer.invoices.filter(
        loyalty_points_status='active'
    ).aggregate(total=models.Sum('loyalty_points'))['total'] or 0

    # Calculate total referral points (active only)
    referral_points = customer.referred_invoices.filter(
        referral_points_status='active'
    ).aggregate(total=models.Sum('referral_points'))['total'] or 0

    return render(request, 'app/customer_detail.html', {
        'customer': customer,
        'customers_invoices': customer.invoices.all().order_by('-date'),
        'referred_invoices': customer.referred_invoices.all().order_by('-date'),
        'loyalty_points': round(loyalty_points, 2),
        'referral_points': round(referral_points, 2),
    })

def loyalty_mark_claimed(request, invoice_id):
    if not request.user.is_authenticated:
        return render(request, 'app/not_loggedin.html')

    try:
        invoice = Invoice.objects.get(iid=invoice_id)
    except Invoice.DoesNotExist:
        messages.error(request, "Invoice not found.")
        return redirect(request.META.get('HTTP_REFERER', '/'))

    if invoice.loyalty_points_status == 'claimed':
        messages.warning(request, "Loyalty points already claimed.")
    else:
        invoice.loyalty_points_status = 'claimed'
        invoice.save()
        messages.success(request, "Loyalty points marked as claimed.")

    return redirect(request.META.get('HTTP_REFERER', '/'))

def referral_mark_claimed(request, invoice_id):
    if not request.user.is_authenticated:
        return render(request, 'app/not_loggedin.html')

    try:
        invoice = Invoice.objects.get(iid=invoice_id)
    except Invoice.DoesNotExist:
        messages.error(request, "Invoice not found.")
        return redirect(request.META.get('HTTP_REFERER', '/'))

    if invoice.referral_points_status == 'claimed':
        messages.warning(request, "Referral points already claimed.")
    else:
        invoice.referral_points_status = 'claimed'
        invoice.save()
        messages.success(request, "Referral points marked as claimed.")

    return redirect(request.META.get('HTTP_REFERER', '/'))

def sales_analytics_page(request):
    if not request.user.is_authenticated:
        return render(request, 'app/not_loggedin.html')
    return render(request, 'app/analytics.html')

@login_required
@require_GET
def sales_api(request):
    start = request.GET.get('start')
    end = request.GET.get('end')

    try:
        start_date = datetime.strptime(start, '%Y-%m-%d').date()
        end_date = datetime.strptime(end, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid or missing date parameters'}, status=400)

    labels = []
    sales_amount = []
    referred_sales_amount = []
    sales_number = []
    referred_sales_number = []

    current_date = start_date
    while current_date <= end_date:
        # All invoices for the day
        invoices = Invoice.objects.filter(date=current_date)
        total_count = invoices.count()
        total_amount = invoices.aggregate(total=Sum('total_amount'))['total'] or 0

        # Invoices with a referrer for the day
        referred_invoices = invoices.filter(referrer__isnull=False)
        referred_count = referred_invoices.count()
        referred_amount = referred_invoices.aggregate(total=Sum('total_amount'))['total'] or 0

        labels.append(current_date.isoformat())
        sales_amount.append(float(total_amount))
        referred_sales_amount.append(float(referred_amount))
        sales_number.append(total_count)
        referred_sales_number.append(referred_count)

        current_date += timedelta(days=1)

    return JsonResponse({
        'labels': labels,
        'sales_amount': sales_amount,
        'referred_sales_amount': referred_sales_amount,
        'sales_number': sales_number,
        'referred_sales_number': referred_sales_number,
    })
