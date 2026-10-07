from decimal import Decimal

from django import forms
from django.utils import timezone

from .models import Expense

DATE_INPUT = forms.DateInput(attrs={"type": "date"})


class ExpenseForm(forms.Form):
    title = forms.CharField(max_length=100, widget=forms.TextInput(attrs={"placeholder": "Coffee at cafe"}))
    amount = forms.DecimalField(
        label="Amount (₹)", min_value=Decimal("0.01"), max_digits=10, decimal_places=2,
        widget=forms.NumberInput(attrs={"step": "0.01"}),
    )
    category = forms.ChoiceField(choices=Expense.Category.choices)
    date = forms.DateField(initial=timezone.localdate, widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"))
    note = forms.CharField(label="Note (optional)", required=False, max_length=1000,
                           widget=forms.Textarea(attrs={"rows": 2}))

    @classmethod
    def for_expense(cls, expense, data=None):
        """Form pre-filled from an existing expense (used by the edit page)."""
        initial = {
            "title": expense.title, "amount": f"{expense.amount:.2f}", "category": expense.category,
            "date": expense.spent_on, "note": expense.note,
        }
        return cls(data, initial=initial)

    def save(self, expense=None) -> Expense:
        """Create a new expense, or update `expense` if one is given."""
        d = self.cleaned_data
        expense = expense or Expense()
        expense.title = d["title"]
        expense.amount_paise = int(d["amount"] * 100)
        expense.category = d["category"]
        expense.spent_on = d["date"]
        expense.note = d["note"]
        expense.save()
        return expense


class FilterForm(forms.Form):
    q = forms.CharField(label="Search title", required=False)
    category = forms.ChoiceField(required=False, choices=[("", "All"), *Expense.Category.choices])
    date_from = forms.DateField(label="From", required=False, widget=DATE_INPUT)
    date_to = forms.DateField(label="To", required=False, widget=DATE_INPUT)

    def clean(self):
        data = super().clean()
        start, end = data.get("date_from"), data.get("date_to")
        if start and end and start > end:
            raise forms.ValidationError("'From' date cannot be after 'To' date.")
        return data
