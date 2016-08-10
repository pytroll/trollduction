"""Classes for handling XYZ for Trollflow based Trollduction"""

import logging

from trollflow.workflow_component import AbstractWorkflowComponent

class TemplateClass(AbstractWorkflowComponent):

    """Do something"""

    logger = logging.getLogger("TemplateClass")

    def __init__(self):
        super(TemplateClass, self).__init__()

    def pre_invoke(self):
        """Pre-invoke"""
        pass

    def invoke(self, context):
        """Invoke"""
        self.logger.info("Doing something.")
        something = do_something_with_content(context["content"])
        context["output_queue"].put(something)

    def post_invoke(self):
        """Post-invoke"""
        pass

def do_something_with_content(something):
    """Do something"""
    return 2 * something
