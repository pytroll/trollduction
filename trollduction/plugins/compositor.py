"""Classes for generating image composites for Trollflow based Trollduction"""

from trollflow.workflow_component import AbstractWorkflowComponent

class CompositeManager(AbstractWorkflowComponent):

    """Creates composites from a product config."""

    def __init__(self):
        super(CompositeManager, self).__init__()

    def pre_invoke(self):
        """Pre-invoke"""
        pass

    @staticmethod
    def invoke(context):
        """Invoke"""
        output_queue = context["output_queue"]
        for prodname in context["products"]:
            func = getattr(context["scene"].image, prodname)
            img = func()
            params = {'prodname': prodname}
            img.info.update(params)
            output_queue.put(img)

    def post_invoke(self):
        """Post-invoke"""
        pass
