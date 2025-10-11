from django.urls import path
from .views import SendVerificationCode, RegistrationConfirm, LoginView, UserDetail, DeleteAccount
from . import views

urlpatterns = [
    path("verification/send/", SendVerificationCode.as_view(), name="send_verification"),
    path("registration/confirm/", RegistrationConfirm.as_view(), name="registration_confirm"),
    path("login/", LoginView.as_view(), name="login"),
    path("user/", UserDetail.as_view(), name="user_detail"),
    path("delete_account/", DeleteAccount.as_view(), name="delete_account"),
    path("password/reset/confirm/", views.PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
]
