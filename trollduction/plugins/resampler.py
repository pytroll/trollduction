"""Classes for generating image composites for Trollflow based Trollduction"""

from trollflow.workflow_component import AbstractWorkflowComponent

class Resampler(AbstractWorkflowComponent):

    """Creates resampled local area scenes."""

    def __init__(self):
        super(Resampler, self).__init__()

    def pre_invoke(self):
        """Pre-invoke"""
        pass

    @staticmethod
    def invoke(context):
        """Invoke"""
        glbl = context["content"]
        for area in glbl.info["product_list"]:
            print "Resampling to area:", area
            lcl = glbl.project(area)
            lcl.info["area"] = area
            lcl.info["products"] = glbl.info["product_list"][area]
            context["output_queue"].put(lcl)

    def post_invoke(self):
        """Post-invoke"""
        pass

