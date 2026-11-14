from django.db import IntegrityError, transaction


class AliasConflictMixin:
    """Two users can pass the alias uniqueness check at the same moment; the DB unique constraint then rejects the
    second save. Turn that IntegrityError into a form error instead of a 500 (data was never at risk)."""

    def form_valid(self, form):
        try:
            with transaction.atomic():
                return super().form_valid(form)
        except IntegrityError:
            form.add_error('custom_url', "This alias was just taken. Please choose another.")
            return self.form_invalid(form)
