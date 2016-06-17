"""Classes for generating image composites for Trollflow based Trollduction"""

from trollflow.workflow_component import AbstractWorkflowComponent

class CompositeGenerator(AbstractWorkflowComponent):

    """Creates composites from a product config."""

    def __init__(self):
        super(CompositeGenerator, self).__init__()

    def pre_invoke(self):
        """Pre-invoke"""
        pass

    @staticmethod
    def invoke(context):
        """Invoke"""
        data = context["content"]
        for prod in data.info["products"]:
            print "Creating composite", prod
            func = getattr(data.image, prod)
            img = func()
            # TODO: Get filename pattern from config?
            file_items = None
            params = None
            context["output_queue"].put((img, file_items, params))
            img.show()

    def post_invoke(self):
        """Post-invoke"""
        pass
