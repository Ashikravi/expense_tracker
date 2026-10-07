from datetime import timedelta
from decimal import Decimal

from django.db.models import Count, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import ExpenseForm, FilterForm
from .models import Expense


def apply_filters(queryset, f):
    """Narrow the queryset using a validated FilterForm. All filters are optional and AND-ed."""
    if f["category"]:
        queryset = queryset.filter(category=f["category"])
    if f["date_from"]:
        queryset = queryset.filter(spent_on__gte=f["date_from"])
    if f["date_to"]:
        queryset = queryset.filter(spent_on__lte=f["date_to"])
    if f["q"].strip():
        #Case-insensitive partial title search.
        queryset = queryset.filter(title__icontains=f["q"].strip())
    return queryset


def month_summary(today):
    start = today.replace(day=1)
    end = (start + timedelta(days=32)).replace(day=1)  # first day of next month
    rows = (
        Expense.objects.filter(spent_on__gte=start, spent_on__lt=end)
        .values("category")
        .annotate(paise=Sum("amount_paise"), count=Count("id"))
        .order_by("-paise")
    )
    total = sum(r["paise"] for r in rows)
    labels = dict(Expense.Category.choices)
    return {
        "total": Decimal(total) / 100,
        "rows": [
            {"label": labels[r["category"]], "count": r["count"],
             "total": Decimal(r["paise"]) / 100, "pct": r["paise"] * 100 / total}
            for r in rows
        ],
    }


def expense_list(request):
    if request.method == "POST":
        form = ExpenseForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect(request.get_full_path())  # post/redirect/get; keeps active filters
    else:
        form = ExpenseForm()

    filter_form = FilterForm(request.GET)  # an empty GET is valid: no filters
    if filter_form.is_valid():
        expenses = apply_filters(Expense.objects.all(), filter_form.cleaned_data)
    else:
        expenses = Expense.objects.none()  # e.g. From > To: show the error, not a misleading list

    today = timezone.localdate()
    return render(request, "expenses/list.html", {
        "form": form,
        "filter_form": filter_form,
        "expenses": expenses,
        "is_filtered": any(request.GET.get(k) for k in FilterForm.base_fields),
        "summary": month_summary(today),
        "month_label": today.strftime("%B %Y"),
    })


def expense_edit(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    data = request.POST if request.method == "POST" else None
    form = ExpenseForm.for_expense(expense, data)
    if form.is_bound and form.is_valid():
        form.save(expense)
        return redirect("expense_list")
    return render(request, "expenses/edit.html", {"form": form, "expense": expense})


def expense_delete(request, pk):
    """GET shows a confirmation page; only POST actually deletes."""
    expense = get_object_or_404(Expense, pk=pk)
    if request.method == "POST":
        expense.delete()
        return redirect("expense_list")
    return render(request, "expenses/confirm_delete.html", {"expense": expense})
