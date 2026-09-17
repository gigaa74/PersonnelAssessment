from django import forms


class InvitationForm(forms.Form):
    email = forms.EmailField(label="E-mail респондента")
    validity_days = forms.IntegerField(label="Срок действия, дней", min_value=1, max_value=30, initial=7)


class ResponseForm(forms.Form):
    value = forms.TypedChoiceField(
        label="",
        coerce=int,
        choices=(),
        widget=forms.RadioSelect,
        error_messages={"required": "Выберите один вариант ответа."},
    )

    def __init__(self, *args, answer_scale, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["value"].choices = tuple(enumerate(answer_scale, 1))

