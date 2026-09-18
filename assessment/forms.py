from django import forms

from .models import Invitation


class InvitationForm(forms.Form):
    full_name = forms.CharField(label="ФИО", max_length=200)
    email = forms.EmailField(label="E-mail респондента")
    participant_type = forms.ChoiceField(label="Тип тестирования", choices=Invitation.ParticipantType.choices)
    department = forms.ChoiceField(label="Подразделение", choices=(("", "Не указано"), *Invitation.Department.choices), required=False)
    position = forms.CharField(label="Должность или вакансия", max_length=160, required=False)
    position_level = forms.ChoiceField(label="Уровень должности", choices=Invitation.PositionLevel.choices)
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


class ConsentForm(forms.Form):
    consent = forms.BooleanField(
        label="Я подтверждаю, что ознакомился с целью оценки и согласен пройти тестирование самостоятельно.",
    )
