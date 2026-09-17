from django.conf import settings
from django.core.mail import send_mail


def send_invitation(email: str, link: str) -> None:
    send_mail(
        "Приглашение пройти оценочный тест",
        "Здравствуйте!\n\n"
        "Вам предложено пройти онлайн-тест оценки профессиональных и управленческих качеств.\n\n"
        f"Для прохождения перейдите по персональной ссылке:\n{link}\n\n"
        "Пожалуйста, отвечайте честно, ориентируясь на обычное поведение в рабочих ситуациях. "
        "Подробные результаты доступны только ответственному администратору.\n\nСпасибо!",
        settings.DEFAULT_FROM_EMAIL,
        [email],
        fail_silently=False,
    )

