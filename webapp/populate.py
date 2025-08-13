import random, string, os, argparse
import django
from datetime import timedelta, date
from tqdm import tqdm, trange

firstnames = [
    "Arindam", "Soumya", "Debanjan", "Ritwik", "Sourav", "Anirban", "Subhankar", "Sayantan", "Partha", "Kaushik",
    "Ankita", "Tania", "Ritika", "Ishita", "Sreemoyee", "Pallavi", "Debopriya", "Mousumi", "Laboni", "Sayani",
    "Indranil", "Prosenjit", "Prasenjit", "Saptarshi", "Avik", "Tanmoy", "Subhasis", "Bappaditya", "Sudip", "Shibaji",
    "Rupam", "Arnab", "Soham", "Debasis", "Swagata", "Bidisha", "Madhumita", "Sumana", "Pritha", "Shreya",
    "Animesh", "Sudeshna", "Sutapa", "Manas", "Kamalika", "Rajat", "Dipankar", "Sourin", "Piyali", "Priyanka"
]

surnames = [
    "Chatterjee", "Mukherjee", "Banerjee", "Ganguly", "Bhattacharya", "Dutta", "Sarkar", "Roy", "Basu", "Sen",
    "Das", "Majumdar", "Nandy", "Mitra", "Ghosh", "Saha", "Pal", "Dey", "Chakraborty", "Biswas",
    "Halder", "Kundu", "Lahiri", "Bagchi", "Kar", "Mondal", "Adhikari", "Mallick", "Hazra", "Sengupta",
    "Choudhury", "Pan", "Samaddar", "Bhowmick", "Debnath", "Bhadra", "Kanjilal", "Sanyal", "Pramanik", "Bairagi",
    "Bhuiyan", "Barua", "Majhi", "Patra", "Rashid", "Haldar", "Chowdhury", "Dasgupta", "Karmakar", "Datta"
]


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()


from app.models import Customer, Invoice
from django.contrib.auth import get_user_model


def random_name(existing_names):
    while True:
        name = random.choice(firstnames) + ' ' + random.choice(surnames)
        if name not in existing_names:
            existing_names.add(name)
            return name

def random_phone(existing_phones):
    while True:
        phone = ''.join(random.choices('0123456789', k=10))
        if phone not in existing_phones:
            existing_phones.add(phone)
            return phone

def generate_customers(n):
    existing_names = set(Customer.objects.values_list('name', flat=True))
    existing_phones = set(Customer.objects.values_list('phone_number', flat=True))
    for i in trange(n):
        cid = str(Customer.objects.count() + 1)
        name = random_name(existing_names)
        phone = random_phone(existing_phones)
        Customer.objects.create(cid=cid, name=name, phone_number=phone)

def generate_invoices(n, start_date, end_date):
    customers = list(Customer.objects.all())
    if not customers:
        print("No customers in database. Please generate customers first.")
        return
    delta_days = (end_date - start_date).days
    for i in trange(n):
        iid = str(Invoice.objects.count() + 1)
        customer = random.choice(customers)
        referrer = None
        if random.random() < 0.2:
            possible_referrers = [c for c in customers if c.cid != customer.cid]
            if possible_referrers:
                referrer = random.choice(possible_referrers)
        total_amount = random.choice(range(1000, 100001, 100))
        invoice_date = start_date + timedelta(days=random.randint(0, delta_days))
        Invoice.objects.create(
            iid=iid,
            customer=customer,
            referrer=referrer,
            total_amount=total_amount,
            date=invoice_date,
            items="some item"
        )


def create_superuser(username, password):
    User = get_user_model()
    if User.objects.filter(username=username).exists():
        print(f"Superuser '{username}' already exists.")
        return
    User.objects.create_superuser(username=username, password=password)
    print(f"Superuser '{username}' created.")


# CLI logic at top-level
parser = argparse.ArgumentParser(description="Populate database with random customers and invoices, or create a superuser.")
parser.add_argument('--customers', type=int, default=0, help='Number of customers to generate')
parser.add_argument('--invoices', type=int, default=0, help='Number of invoices to generate')
parser.add_argument('--days', type=int, default=30, help='Number of days in the past for invoice dates')
parser.add_argument('--superuser', action='store_true', help='Create a superuser')
parser.add_argument('--username', type=str, help='Superuser username')
parser.add_argument('--password', type=str, help='Superuser password')

args = parser.parse_args()

if args.superuser:
    if not args.username or not args.password:
        print("--username and --password are required for superuser creation.")
    else:
        create_superuser(args.username, args.password)
        print(f"Superuser '{args.username}' created.")

if args.customers > 0:
    generate_customers(args.customers)
    print(f"Generated {args.customers} customers.")

if args.invoices > 0:
    today = date.today()
    start_date = today - timedelta(days=args.days)
    generate_invoices(args.invoices, start_date, today)
    print(f"Generated {args.invoices} invoices from {start_date} to {today}.")
