"""
Test factories for generating test data.
"""

import factory
from factory.django import DjangoModelFactory
from kanban.models import Column, Task


class ColumnFactory(DjangoModelFactory):
    """Factory for creating Column instances."""
    
    class Meta:
        model = Column
    
    name = factory.Sequence(lambda n: f"Column {n}")
    order = factory.Sequence(lambda n: n)


class TaskFactory(DjangoModelFactory):
    """Factory for creating Task instances."""
    
    class Meta:
        model = Task
    
    title = factory.Sequence(lambda n: f"Task {n}")
    description = factory.Faker('paragraph', nb_sentences=2)
    column = factory.SubFactory(ColumnFactory)
    order = factory.Sequence(lambda n: n)
