"""Classes for data enhancements Trollflow based Trollduction"""

import numpy as np
import logging

from trollflow.workflow_component import AbstractWorkflowComponent

class Pansharpener(AbstractWorkflowComponent):

    """Pansharpen the configured channels"""

    logger = logging.getLogger("Pansharpener")

    def __init__(self):
        super(Pansharpener, self).__init__()

    def pre_invoke(self):
        """Pre-invoke"""
        pass

    def invoke(self, context):
        """Invoke"""
        glbl = context["content"]
        # Read list of channels to be sharpened
        pan_chans = context["pan_sharpen_chans"]["content"]
        self.logger.info("Applying pansharpening to channels: %s",
                         str(pan_chans))
        # Check if the original data should be overwritten (default)
        # or create a new channel named "pan_"+chan.name
        try:
            overwrite = context["overwrite"]["content"]
        except KeyError:
            overwrite = True

        if overwrite:
            self.logger.info("Original data will be overwritten.")
        else:
            self.logger.info("Pansharpened channels will be named with "
                             "'pan_' prefix.")

        # Apply pansharpening
        pansharpen(glbl, pan_chans, overwrite)

        # Put enhanced data to output queue
        context["output_queue"].put(glbl)

    def post_invoke(self):
        """Post-invoke"""
        pass

def pansharpen(glbl, pan_chans, overwrite=True):
    """Apply pansharpening"""
    hrv = glbl["HRV"].data

    # Pad HRV data, if shape isn't divisible by three
    hrv_orig_shape = hrv.shape
    y_rem = hrv_orig_shape[0] % 3
    x_rem = hrv_orig_shape[1] % 3
    if y_rem != 0:
        hrv = np.vstack((hrv, hrv[-(3-y_rem):, :]))
    if x_rem != 0:
        hrv = np.hstack((hrv, hrv[:, -(3-x_rem):]))

    shape = hrv.shape
    highresr = np.roll(np.roll(hrv, -1, axis=0), -2, axis=1)
    lowres = highresr.reshape([shape[0]/3, 3, shape[1]/3, 3]).mean(3).mean(1)
    highres = np.ma.repeat(np.ma.repeat(lowres, 3, axis=0), 3, axis=1)
    ratio = highresr / highres
    # Cut to original HRV shape
    # ratio = ratio[0:hrv_orig_shape[0], 0:hrv_orig_shape[1]]

    # Cut to original HRV shape
    glbl["HRV"].data = highresr[0:hrv_orig_shape[0], 0:hrv_orig_shape[1]]

    for chan_name in pan_chans:
        chan = 1.0 * glbl[chan_name]

        # Pad data if shape isn't divisible by three
        shape = chan.data.shape
        y_rem = shape[0] % 3
        x_rem = shape[1] % 3
        if y_rem != 0:
            chan.data = np.vstack((chan.data, chan.data[-(3-y_rem):, :]))
        if x_rem != 0:
            chan.data = np.hstack((chan.data, chan.data[:, -(3-x_rem):]))

        # Replicate data
        chan.data = np.ma.repeat(np.ma.repeat(chan.data, 3, axis=0), 3, axis=1)

        # Adjust to original HRV shape
        shape = chan.data.shape
        y_diff, x_diff = ratio.shape[0], ratio.shape[1]
        if y_diff != 0:
            # Add pixels
            if y_diff > 0:
                chan.data = np.vstack((chan.data, chan.data[-y_diff:, :]))
            # Cut extra pixels
            else:
                chan.data = chan.data[:-y_diff, :]
        if x_diff != 0:
            # Add pixels
            if x_diff > 0:
                chan.data = np.hstack((chan.data, chan.data[:, -x_diff:]))
            # Cut extra pixels
            else:
                chan.data = chan.data[:, :-x_diff]

        # Cut the data to original HRV shape and apply sharpening
        chan.data = chan.data[0:hrv_orig_shape[0], 0:hrv_orig_shape[1]]
        chan.data *= ratio[0:hrv_orig_shape[0], 0:hrv_orig_shape[1]]

        # Either overwrite the data, or create a new channel
        if overwrite:
            glbl[chan_name].data = chan.data
        else:
            chan_name = "pan_" + chan_name
            chan.name = chan_name
            glbl.channels.append(chan)

        # Replace area definition with HRV area def
        glbl[chan_name].area = glbl["HRV"].area
