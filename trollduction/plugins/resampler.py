"""Classes for generating image composites for Trollflow based Trollduction"""

import logging

from trollflow.workflow_component import AbstractWorkflowComponent
from trollduction.xml_read import ProductList


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
        product_config = ProductList(context["product_list"]["content"])

        # Handle config options
        try:
            precompute = context["precompute"]["content"]
            self.logger.debug("Setting precompute to %s", str(precompute))
        except KeyError:
            precompute = False
        try:
            nprocs = context["nprocs"]["content"]
            self.logger.debug("Using %d CPUs for resampling.", nprocs)
        except KeyError:
            nprocs = 1
        try:
            proj_method = context["proj_method"]["content"]
            self.logger.debug("Using resampling method: '%s'.", proj_method)
        except KeyError:
            proj_method = "nearest"
        try:
            radius = context["radius"]["content"]
            if radius is None:
                self.logger.debug("Using default search radius.")
            else:
                self.logger.debug("Using search radius %d meters.",
                                  int(radius))
        except KeyError:
            radius = None

        for area_name in glbl.info["product_list"]:
            # Reproject only needed channels
            channels = get_prerequisites_xml(glbl, product_config, area_name)
            self.logger.info("Resampling to area %s", area_name)
            lcl = glbl.project(area_name, channels=channels,
                               precompute=precompute,
                               mode=proj_method, radius=radius, nprocs=nprocs)
            lcl.info["areaname"] = area_name
            lcl.info["products"] = glbl.info["product_list"][area_name]
            context["output_queue"].put(lcl)
            del lcl
            lcl = None

    def post_invoke(self):
        """Post-invoke"""
        pass


def get_prerequisites_xml(global_data, product_config, area_name):
    """Get composite prerequisite channels for a group"""
    reqs = set()
    for group in product_config.groups:
        for area in group.data:
            if area.attrib["name"] != area_name:
                continue
            for product in area:
                try:
                    composite = getattr(global_data.image,
                                        product.attrib['id'])
                except AttributeError:
                    continue
                reqs |= composite.prerequisites
    return reqs
