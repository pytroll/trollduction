"""Classes for generating image composites for Trollflow based Trollduction"""

import logging

from trollflow.workflow_component import AbstractWorkflowComponent

class Resampler(AbstractWorkflowComponent):

    """Creates resampled local area scenes."""

    logger = logging.getLogger("Resampler")

    def __init__(self):
        super(Resampler, self).__init__()

    def pre_invoke(self):
        """Pre-invoke"""
        pass

    def invoke(self, context):
        """Invoke"""
        glbl = context["content"]
        for area in glbl.info["product_list"]:
            self.logger.info("Resampling to area %s", area)
            lcl = glbl.project(area)
            lcl.info["area"] = area
            lcl.info["products"] = glbl.info["product_list"][area]
            context["output_queue"].put(lcl)

    def post_invoke(self):
        """Post-invoke"""
        pass

