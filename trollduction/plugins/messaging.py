
"""Classes for handling messaging for Trollflow based Trollduction"""

from trollflow.workflow_component import AbstractWorkflowComponent
from mpop.satellites import GenericFactory as GF
from trollduction.xml_read import ProductList
import logging

class MessageLoader(AbstractWorkflowComponent):

    """Creates a scene object from a message."""

    logger = logging.getLogger("MessageLoader")

    def __init__(self):
        super(MessageLoader, self).__init__()

    def pre_invoke(self):
        """Pre-invoke"""
        pass

    def invoke(self, context):
        """Invoke"""
        global_data = self.create_scene_from_message(context['content'])
        global_data.info['product_list'] = {}
        product_config = ProductList(context["product_list"]["content"])

        for group in product_config.groups:
            grp_area_def_names = [item.attrib["id"]
                                  for item in group.data
                                  if item.tag == "area"]
            reqs = get_prerequisites_xml(global_data, group.data)
            self.logger.info("Loading required channels for this group: %s",
                             str(sorted(reqs)))
            global_data.load(reqs, area_def_names=grp_area_def_names)
            for area_item in group.data:
                global_data.info["product_list"][area_item.attrib['id']] = \
                        [item.attrib["id"] for \
                         item in area_item if item.tag == "product"]

            context["output_queue"].put(global_data)

    def post_invoke(self):
        """Post-invoke"""
        pass

    def create_scene_from_message(self, msg):
        """Parse the message *msg* and return a corresponding MPOP scene.
        """
        if msg.type in ["file", 'collection', 'dataset']:
            return self.create_scene_from_mda(msg.data)

    def create_scene_from_mda(self, mda):
        """Read the metadata *mda* and return a corresponding MPOP scene.
        """
        time_slot = (mda.get('start_time') or
                     mda.get('nominal_time') or
                     mda.get('end_time'))

        # orbit is not given for GEO satellites, use None
        if 'orbit_number' not in mda:
            mda['orbit_number'] = None

        platform = mda["platform_name"]

        self.logger.debug("platform %s time %s", str(platform), str(time_slot))

        if isinstance(mda['sensor'], (list, tuple, set)):
            sensor = mda['sensor'][0]
        else:
            sensor = mda['sensor']

        # Create satellite scene
        global_data = GF.create_scene(satname=str(platform),
                                      satnumber='',
                                      instrument=str(sensor),
                                      time_slot=time_slot,
                                      orbit=mda['orbit_number'],
                                      variant=mda.get('variant', ''))
        self.logger.info("Creating scene for satellite %s and time %s",
                         str(platform), str(time_slot))

        # Update missing information to global_data.info{}
        # TODO: this should be fixed in mpop.
        global_data.info.update(mda)
        global_data.info['time'] = time_slot

        return global_data

def get_prerequisites_xml(global_data, grp_config):
    """Get composite prerequisite channels for a group"""
    reqs = set()
    for area in grp_config:
        for product in area:
            composite = getattr(global_data.image, product.attrib['id'])
            reqs |= composite.prerequisites
    return reqs
