"""Classes for handling XYZ for Trollflow based Trollduction"""

from trollflow.workflow_component import AbstractWorkflowComponent

class TemplateClass(AbstractWorkflowComponent):

    """Do something"""

    def __init__(self):
        super(TemplateClass, self).__init__()

    def pre_invoke(self):
        """Pre-invoke"""
        pass

    @staticmethod
    def invoke(context):
        """Invoke"""
        context["something"] = do_something()

    def post_invoke(self):
        """Post-invoke"""
        pass

def do_something():
    """Do something"""
    return "something"
