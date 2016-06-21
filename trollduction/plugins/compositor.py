"""Classes for generating image composites for Trollflow based Trollduction"""

import os.path
import logging

from trollflow.workflow_component import AbstractWorkflowComponent
from trollduction.xml_read import ProductList
from trollsift import compose

class CompositeGenerator(AbstractWorkflowComponent):

    """Creates composites from a product config."""

    logger = logging.getLogger("Compositor")

    def __init__(self):
        super(CompositeGenerator, self).__init__()

    def pre_invoke(self):
        """Pre-invoke"""
        pass

    def invoke(self, context):
        """Invoke"""
        data = context["content"]
        prod_list = ProductList(context["product_list"]["content"])
        for prod in data.info["products"]:
            self.logger.info("Creating composite %s", prod)
            func = getattr(data.image, prod)
            img = func()
            # Get filename from product config
            fname = create_fname(data.info, prod_list, prod)
            if fname is None:
                self.logger.error("Could not generate a valid filename, "
                                  "product not saved!")
            else:
                context["output_queue"].put((img, fname))
            # img.show()

    def post_invoke(self):
        """Post-invoke"""
        pass

def create_fname(info, prod_list, prod):
    """Create filename for product *prod*"""
    area = info["area"]
    info["productname"] = prod
    info["areaname"] = area
    pattern = _get_pattern_xml(prod_list, area, prod)
    if pattern is not None:
        return compose(pattern, info)
    else:
        return None

def _get_pattern_xml(prod_list, area_name, prod_name):
    """Get filepattern for area *area* and product *prod*"""
    for grp in prod_list.groups:
        for area in grp.data:
            if area.attrib["name"] != area_name:
                continue
            for product in area:
                if product.attrib["name"] == prod_name:
                    output_dir = \
                        product.attrib.get("output_dir",
                                           prod_list.attrib["output_dir"])
                    return os.path.join(output_dir, product[0].text)
    return None
