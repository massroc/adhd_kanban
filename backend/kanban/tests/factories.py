"""
Test factories for generating test data.
"""

import factory
from factory.django import DjangoModelFactory
from django.contrib.auth import get_user_model
from kanban.models import Column, Task

User = get_user_model()


class UserFactory(DjangoModelFactory):
    """Factory for creating User instances."""
    
    class Meta:
        model = User
        skip_postgeneration_save = True
    
    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
    
    @factory.post_generation
    def password(obj, create, extracted, **kwargs):
        """Set password and save. Default password is 'testpass123'."""
        password = extracted or 'testpass123'
        obj.set_password(password)
        if create:
            obj.save()


class ColumnFactory(DjangoModelFactory):
    """Factory for creating Column instances."""
    
    class Meta:
        model = Column
    
    user = factory.SubFactory(UserFactory)
    name = factory.Sequence(lambda n: f"Column {n}")
    order = factory.Sequence(lambda n: n)


class TaskFactory(DjangoModelFactory):
    """Factory for creating Task instances."""
    
    class Meta:
        model = Task
    
    user = factory.LazyAttribute(lambda obj: obj.column.user)
    title = factory.Sequence(lambda n: f"Task {n}")
    description = factory.Faker('paragraph', nb_sentences=2)
    column = factory.SubFactory(ColumnFactory)
    order = factory.Sequence(lambda n: n)
