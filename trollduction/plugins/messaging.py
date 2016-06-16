
"""Classes for handling messaging"""

from trollflow.workflow_component import AbstractWorkflowComponent
from mpop.satellites import GenericFactory as GF

class MessageLoader(AbstractWorkflowComponent):

    """Creates a scene object from a message."""

    def pre_invoke(self):
        """Pre invoke"""
        pass

    @staticmethod
    def invoke(context):
        """Invoke"""
        context['global_data'] = create_scene_from_message(context)

    def post_invoke(self):
        """Post-invoke"""
        pass

def create_scene_from_message(msg):
    """Parse the message *msg* and return a corresponding MPOP scene.
    """
    if msg.type in ["file", 'collection', 'dataset']:
        return create_scene_from_mda(msg.data)

def create_scene_from_mda(mda):
    """Read the metadata *mda* and return a corresponding MPOP scene.
    """
    time_slot = (mda.get('start_time') or
                 mda.get('nominal_time') or
                 mda.get('end_time'))

    # orbit is not given for GEO satellites, use None
    if 'orbit_number' not in mda:
        mda['orbit_number'] = None

    platform = mda["platform_name"]

    print "platform %s time %s" % (str(platform), str(time_slot))

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
    print "Creating scene for satellite %s and time %s" % \
        (str(platform), str(time_slot))

    # Update missing information to global_data.info{}
    # TODO: this should be fixed in mpop.
    global_data.info.update(mda)
    global_data.info['time'] = time_slot

    return global_data
