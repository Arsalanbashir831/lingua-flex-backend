import uuid
from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    PermissionsMixin,
    BaseUserManager,
)


class SupabaseUserManager(BaseUserManager):
    def create_user(self, id, email, username=None, **extra_fields):
        """
        We already get the id from Supabase, so we require it.
        Password is not used (Supabase handles auth), but AbstractBaseUser needs something,
        so set unusable password.
        """
        if not id:
            raise ValueError("Supabase user must have an id")
        if not email:
            raise ValueError("Supabase user must have an email")

        email = self.normalize_email(email)
        user = self.model(
            id=id, email=email, username=username or email.split("@")[0], **extra_fields
        )
        user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_oauth_user(
        self,
        id,
        email,
        first_name=None,
        last_name=None,
        auth_provider="GOOGLE",
        **extra_fields,
    ):
        """
        Create user from OAuth provider (Google, etc.)
        These users are automatically verified
        """
        if not id:
            raise ValueError("OAuth user must have an id")
        if not email:
            raise ValueError("OAuth user must have an email")

        email = self.normalize_email(email)
        username = username = email.split("@")[0]

        # Set OAuth-specific defaults
        extra_fields.setdefault("is_oauth_user", True)
        extra_fields.setdefault("email_verified", True)
        extra_fields.setdefault("auth_provider", auth_provider)

        user = self.model(
            id=id,
            email=email,
            username=username,
            first_name=first_name,
            last_name=last_name,
            **extra_fields,
        )
        user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Let you create a Django admin superuser manually (no Supabase id). We'll fabricate a UUID.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        supa_id = uuid.uuid4().hex
        user = self.model(
            id=supa_id,
            email=self.normalize_email(email),
            username=email.split("@")[0],
            **extra_fields,
        )
        user.set_password(password or uuid.uuid4().hex)
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        STUDENT = "STUDENT", "Student"
        TEACHER = "TEACHER", "Teacher"
        BOTH = "BOTH", "Both Student and Teacher"
        ADMIN = "ADMIN", "Administrator"

    class AuthProvider(models.TextChoices):
        EMAIL = "EMAIL", "Email/Password"
        GOOGLE = "GOOGLE", "Google OAuth"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, blank=True, null=True)
    first_name = models.CharField(max_length=30, blank=True, null=True)
    last_name = models.CharField(max_length=150, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    gender = models.CharField(max_length=20, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    profile_picture = models.ImageField(
        upload_to="profile_pictures/", blank=True, null=True
    )
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.STUDENT)

    # OAuth fields
    auth_provider = models.CharField(
        max_length=20, choices=AuthProvider.choices, default=AuthProvider.EMAIL
    )
    google_id = models.CharField(max_length=100, blank=True, null=True, unique=True)
    is_oauth_user = models.BooleanField(default=False)
    email_verified = models.BooleanField(default=False)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(blank=True, null=True)

    objects = SupabaseUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def __str__(self):
        return f"{self.email} ({self.id})"

    def get_full_name(self):
        """Return the full name of the user"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}".strip()
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        else:
            return self.username or self.email.split("@")[0]

    def has_teacher(self):
        """Return True if the user has a TeacherProfile."""
        from accounts.models import TeacherProfile

        return TeacherProfile.objects.filter(user_profile__user=self).exists()

    def has_student(self):
        """Return True if the user registered as a student or opted into both."""
        return self.role in [self.Role.STUDENT, self.Role.BOTH]

    def create_teacher_profile(self):
        """Create accounts.TeacherProfile for this user.

        Returns the TeacherProfile instance.
        """
        from django.db import transaction
        from accounts.models import (
            UserProfile,
            TeacherProfile as AccountsTeacherProfile,
        )

        with transaction.atomic():
            # Ensure UserProfile exists
            user_profile = getattr(self, "profile", None)
            if user_profile is None:
                user_profile = UserProfile.objects.create(user=self)

            # Create accounts.TeacherProfile if missing
            tp = None
            try:
                tp = user_profile.teacherprofile
            except Exception:
                tp = AccountsTeacherProfile.objects.create(
                    user_profile=user_profile,
                    qualification="",
                    experience_years=0,
                    certificates=[],
                    about="",
                    teaching_languages=[],
                    hourly_rate=0,
                    is_verified=False,
                )

        return tp
