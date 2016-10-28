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
            try:
                func = getattr(data.image, prod)
                img = func()
                if img is None:
                    continue
                img.info.update(data.info)
            except (AttributeError, KeyError):
                self.logger.warning("Invalid composite, skipping")
                continue

            # Get filename and product name from product config
            fname, productname = create_fname(data.info, prod_list, prod)

            if fname is None:
                self.logger.error("Could not generate a valid filename, "
                                  "product not saved!")
            else:
                context["output_queue"].put((img, fname, productname))
            del img
            img = None

    def post_invoke(self):
        """Post-invoke"""
        pass


def create_fname(info, prod_list, prod_name):
    """Create filename for product *prod*"""
    area_name = info["areaname"]

    pattern, prod_name = _get_pattern_and_prodname_xml(prod_list,
                                                       area_name,
                                                       prod_name)
    info["productname"] = prod_name
    if pattern is not None:
        return (compose(pattern, info), prod_name)
    else:
        return (None, prod_name)


def _get_pattern_and_prodname_xml(prod_list, area_name, prod_name):
    """Get filepattern for area *area* and product *prod*"""
    for grp in prod_list.groups:
        for area in grp.data:
            # FIXME: area name might be different than the projection name
            if area.attrib["name"] != area_name:
                continue
            for product in area:
                # FIXME: prod_name might be something different
                if product.attrib["name"] in prod_name:
                    output_dir = \
                        product.attrib.get("output_dir",
                                           prod_list.attrib["output_dir"])
                    return (os.path.join(output_dir, product[0].text),
                            product.attrib["name"])
    return None, None
