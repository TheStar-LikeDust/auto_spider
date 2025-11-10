"""
Base component module for auto_spider.

Base component system including Component class, metaclass and utilities.

Component Base:
    Every component needs two common methods: on_start and on_exit,
    called on startup and exit for resource management.

    Three common attributes:
        1. name: auto-generated, used to identify component
        2. active: default False, enabled via decorator
        3. priority: 0-1000 integer, controls component execution order

Note:
    All components must inherit from Component base class.

Utilities:
    1. active - decorator to activate component (active == True)
    2. set_active - function to activate component class
"""

from abc import abstractmethod
from typing import NoReturn, Type

from auto_spider.logger import build_logger


class ComponentMeta(type):
    """
    Metaclass for Component to append common properties.
    
    Automatically adds 'active' and 'name' attributes to component classes.
    """

    def __new__(mcs, name, bases, attrs: dict):
        if attrs.get("_active") is None:
            attrs["active"] = False
        attrs["name"] = name
        return type.__new__(mcs, name, bases, attrs)


class Component(object, metaclass=ComponentMeta):
    """
    Base component class for all components.
    
    Provides common methods and attributes for component lifecycle management.
    
    Note:
        Do not modify Component attributes directly, use utility functions.
    """
    active: bool
    """Component activation state."""
    
    name: str
    """Component name."""
    
    priority: int = 500
    """Component priority for execution order."""

    @abstractmethod
    def on_start(self) -> NoReturn:
        """Called when component starts."""
        pass

    @abstractmethod
    def on_exit(self) -> NoReturn:
        """Called when component exits."""
        pass


def active(component_class: Type[Component]):
    """
    Decorator to activate component class.
    
    Args:
        component_class: Component class to activate
        
    Returns:
        Activated component class
    """
    component_class.active = True
    return component_class


def set_active(component_class: Type[Component]):
    """
    Manually activate component class.
    
    Args:
        component_class: Component class to activate
    """
    component_class.active = True


logger = build_logger('component')
